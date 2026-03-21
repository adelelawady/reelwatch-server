#!/usr/bin/env python3
"""
ReelWatch Server v2 — with rooms, users, remote control & rich dashboard
Run with: python server2.py
"""

import asyncio
import json
import socket
import time
import threading
from dataclasses import dataclass, field
from typing import Optional
import websockets
from websockets.server import WebSocketServerProtocol

# ── Rich imports ─────────────────────────────────────────────────────────────
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.style import Style
from rich.align import Align
from rich.rule import Rule

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
PORT = 3001
console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class User:
    name: str
    ws: WebSocketServerProtocol
    room_id: Optional[str] = None
    joined_at: float = field(default_factory=time.time)
    current_reel: str = "—"


@dataclass
class Room:
    room_id: str
    owner_name: str
    remote_control: bool          # True = only controller can push reels
    controller_name: str = ""     # who currently holds remote
    created_at: float = field(default_factory=time.time)
    users: dict = field(default_factory=dict)   # name → User
    current_reel: str = "—"

    def __post_init__(self):
        if self.remote_control:
            self.controller_name = self.owner_name  # owner starts with remote


# ═══════════════════════════════════════════════════════════════════════════════
# SERVER STATE
# ═══════════════════════════════════════════════════════════════════════════════

class ServerState:
    def __init__(self):
        self.lock = asyncio.Lock()
        # ws → User (connected but not yet in a room)
        self.connections: dict[WebSocketServerProtocol, User] = {}
        # room_id → Room
        self.rooms: dict[str, Room] = {}
        self.log_lines: list[str] = []
        self.start_time = time.time()

    def add_log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log_lines.append(f"[dim]{ts}[/dim] {msg}")
        if len(self.log_lines) > 80:
            self.log_lines = self.log_lines[-80:]

    def get_user_by_ws(self, ws) -> Optional[User]:
        return self.connections.get(ws)

    def get_user_by_name(self, name: str) -> Optional[User]:
        for u in self.connections.values():
            if u.name == name:
                return u
        return None

    @property
    def total_users(self):
        return len(self.connections)

    @property
    def total_rooms(self):
        return len(self.rooms)


state = ServerState()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def send(ws: WebSocketServerProtocol, msg: dict):
    """Send a message to a single client, ignore if closed."""
    try:
        await ws.send(json.dumps(msg))
    except Exception:
        pass


async def broadcast_room(room_id: str, msg: dict, skip: Optional[WebSocketServerProtocol] = None):
    """Broadcast to everyone in a room."""
    room = state.rooms.get(room_id)
    if not room:
        return
    dead = []
    for user in list(room.users.values()):
        if user.ws is skip:
            continue
        try:
            await user.ws.send(json.dumps(msg))
        except Exception:
            dead.append(user.name)
    for name in dead:
        room.users.pop(name, None)


async def broadcast_all(msg: dict):
    """Broadcast to every connected client."""
    dead = []
    for ws, user in list(state.connections.items()):
        try:
            await ws.send(json.dumps(msg))
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.connections.pop(ws, None)


def rooms_list_payload():
    """Build the room list payload sent to clients."""
    rooms = []
    for r in state.rooms.values():
        rooms.append({
            "id": r.room_id,
            "owner": r.owner_name,
            "remote_control": r.remote_control,
            "controller": r.controller_name if r.remote_control else None,
            "users": list(r.users.keys()),
            "user_count": len(r.users),
            "current_reel": r.current_reel,
        })
    return {"type": "rooms_list", "rooms": rooms}


def room_state_payload(room: Room):
    """Build full room state for a specific room."""
    return {
        "type": "room_state",
        "room": {
            "id": room.room_id,
            "owner": room.owner_name,
            "remote_control": room.remote_control,
            "controller": room.controller_name if room.remote_control else None,
            "users": list(room.users.keys()),
            "user_count": len(room.users),
            "current_reel": room.current_reel,
        }
    }


async def push_rooms_list_to_all():
    """Push updated room list to every connected client."""
    payload = rooms_list_payload()
    await broadcast_all(payload)


async def push_room_state(room: Room):
    """Push updated room state to everyone inside that room."""
    payload = room_state_payload(room)
    await broadcast_room(room.room_id, payload)


def extract_reel_id(url: str) -> str:
    parts = url.split("/reels/")
    if len(parts) > 1:
        return parts[1].replace("/", "").split("?")[0]
    return url[:40]


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_register(ws, msg):
    """Client sends: { type: 'register', name: 'Alice' }"""
    name = (msg.get("name") or "").strip()
    if not name:
        await send(ws, {"type": "error", "code": "NAME_REQUIRED", "msg": "Name is required."})
        return

    # Check name uniqueness — connections only contains real User objects now
    if any(u.name == name for u in state.connections.values()):
        await send(ws, {"type": "error", "code": "NAME_TAKEN", "msg": f"Name '{name}' is already taken."})
        return

    user = User(name=name, ws=ws)
    state.connections[ws] = user
    state.add_log(f"[green]✚[/green] [bold]{name}[/bold] connected")

    await send(ws, {"type": "registered", "name": name})
    # Send current room list immediately
    await send(ws, rooms_list_payload())


async def handle_create_room(ws, msg, user: User):
    """Client sends: { type: 'create_room', room: 'id', remote_control: bool }"""
    room_id = (msg.get("room") or "").strip()
    if not room_id:
        await send(ws, {"type": "error", "code": "ROOM_ID_REQUIRED", "msg": "Room ID is required."})
        return
    if room_id in state.rooms:
        await send(ws, {"type": "error", "code": "ROOM_EXISTS", "msg": f"Room '{room_id}' already exists."})
        return

    remote = bool(msg.get("remote_control", False))
    room = Room(room_id=room_id, owner_name=user.name, remote_control=remote)
    state.rooms[room_id] = room
    state.add_log(f"[cyan]🏠[/cyan] [bold]{user.name}[/bold] created room [yellow]{room_id}[/yellow] (remote={'on' if remote else 'off'})")

    await send(ws, {"type": "room_created", "room": room_id})
    await push_rooms_list_to_all()


async def handle_delete_room(ws, msg, user: User):
    """Client sends: { type: 'delete_room', room: 'id' }"""
    room_id = msg.get("room", "")
    room = state.rooms.get(room_id)
    if not room:
        await send(ws, {"type": "error", "code": "ROOM_NOT_FOUND", "msg": "Room not found."})
        return
    if room.owner_name != user.name:
        await send(ws, {"type": "error", "code": "NOT_OWNER", "msg": "Only the room owner can delete it."})
        return

    # Kick everyone out of the room
    await broadcast_room(room_id, {"type": "room_deleted", "room": room_id, "reason": "Owner deleted the room."})
    for u in list(room.users.values()):
        u.room_id = None
    del state.rooms[room_id]
    state.add_log(f"[red]🗑[/red] [bold]{user.name}[/bold] deleted room [yellow]{room_id}[/yellow]")

    await push_rooms_list_to_all()


async def handle_join(ws, msg, user: User):
    """Client sends: { type: 'join', room: 'id' }"""
    room_id = msg.get("room", "")
    room = state.rooms.get(room_id)
    if not room:
        await send(ws, {"type": "error", "code": "ROOM_NOT_FOUND", "msg": f"Room '{room_id}' not found."})
        return

    # Leave old room if in one
    if user.room_id and user.room_id != room_id:
        old_room = state.rooms.get(user.room_id)
        if old_room:
            old_room.users.pop(user.name, None)
            await push_room_state(old_room)
            state.add_log(f"[dim]{user.name} left {user.room_id}[/dim]")

    user.room_id = room_id
    room.users[user.name] = user
    state.add_log(f"[blue]→[/blue] [bold]{user.name}[/bold] joined room [yellow]{room_id}[/yellow] ({len(room.users)} users)")

    await send(ws, {"type": "joined", "room": room_id})
    await push_room_state(room)
    await push_rooms_list_to_all()


async def handle_leave(ws, msg, user: User):
    """Client sends: { type: 'leave' }"""
    if not user.room_id:
        return
    room = state.rooms.get(user.room_id)
    if room:
        room.users.pop(user.name, None)
        # Transfer remote if needed
        if room.remote_control and room.controller_name == user.name:
            room.controller_name = room.owner_name
            state.add_log(f"[yellow]🎮[/yellow] Remote auto-transferred to owner [bold]{room.owner_name}[/bold]")
        state.add_log(f"[dim]← {user.name} left {user.room_id}[/dim]")
        await push_room_state(room)
        await push_rooms_list_to_all()
    user.room_id = None


async def handle_transfer_remote(ws, msg, user: User):
    """Owner passes remote to another user. { type: 'transfer_remote', to: 'name' }"""
    if not user.room_id:
        return
    room = state.rooms.get(user.room_id)
    if not room or not room.remote_control:
        await send(ws, {"type": "error", "code": "NO_REMOTE", "msg": "Room has no remote control feature."})
        return
    if room.controller_name != user.name:
        await send(ws, {"type": "error", "code": "NOT_CONTROLLER", "msg": "You don't hold the remote."})
        return

    target = msg.get("to", "")
    if target not in room.users:
        await send(ws, {"type": "error", "code": "USER_NOT_IN_ROOM", "msg": f"'{target}' is not in this room."})
        return

    room.controller_name = target
    state.add_log(f"[magenta]🎮[/magenta] Remote: [bold]{user.name}[/bold] → [bold]{target}[/bold] in [yellow]{room.room_id}[/yellow]")

    await broadcast_room(room.room_id, {
        "type": "remote_transferred",
        "from": user.name,
        "to": target,
        "room": room.room_id,
    })
    await push_room_state(room)


async def handle_reel_update(ws, msg, user: User, msg_type: str):
    """
    Handles: url, reel_url, reel_src, reel_index
    If remote_control is on, only the controller can broadcast reel changes.
    """
    if not user.room_id:
        return
    room = state.rooms.get(user.room_id)
    if not room:
        return

    # Remote control gate
    if room.remote_control and room.controller_name != user.name:
        # Silently drop — non-controller scroll events are ignored
        return

    # Track current reel for dashboard
    if msg_type in ("url", "reel_url"):
        reel_id = extract_reel_id(msg.get("url", ""))
        room.current_reel = reel_id
        user.current_reel = reel_id
    elif msg_type == "reel_index":
        room.current_reel = f"#{msg.get('index', '?')}"
        user.current_reel = room.current_reel

    await broadcast_room(room.room_id, msg, skip=ws)


async def handle_comment(ws, msg, user: User):
    if not user.room_id:
        return
    room = state.rooms.get(user.room_id)
    if not room:
        return
    text = msg.get("text", "")
    state.add_log(f"[green]💬[/green] [bold]{user.name}[/bold] @ [yellow]{user.room_id}[/yellow]: {text[:60]}")
    await broadcast_room(user.room_id, {**msg, "from": user.name}, skip=ws)


async def handle_list_rooms(ws, msg, user: User):
    await send(ws, rooms_list_payload())


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_connection(ws: WebSocketServerProtocol):
    # Do NOT pre-insert ws — only added to state.connections after successful register
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            async with state.lock:
                # Always read user fresh inside the lock so we see post-register state
                user: Optional[User] = state.connections.get(ws)

                # ── register (must be first) ───────────────────────────────
                if msg_type == "register":
                    await handle_register(ws, msg)

                # ── all other messages require registration ────────────────
                elif user is None:
                    await send(ws, {"type": "error", "code": "NOT_REGISTERED",
                                    "msg": "Send register with your name first."})

                elif msg_type == "create_room":
                    await handle_create_room(ws, msg, user)

                elif msg_type == "delete_room":
                    await handle_delete_room(ws, msg, user)

                elif msg_type == "join":
                    await handle_join(ws, msg, user)

                elif msg_type == "leave":
                    await handle_leave(ws, msg, user)

                elif msg_type == "transfer_remote":
                    await handle_transfer_remote(ws, msg, user)

                elif msg_type in ("url", "reel_url", "reel_src", "reel_index"):
                    await handle_reel_update(ws, msg, user, msg_type)

                elif msg_type == "comment":
                    await handle_comment(ws, msg, user)

                elif msg_type == "list_rooms":
                    await handle_list_rooms(ws, msg, user)

    except websockets.ConnectionClosed:
        pass
    except Exception as exc:
        state.add_log(f"[red]⚠ connection error:[/red] {exc}")
    finally:
        async with state.lock:
            user = state.connections.pop(ws, None)
            if user:
                state.add_log(f"[red]✖[/red] [bold]{user.name}[/bold] disconnected")
                if user.room_id:
                    room = state.rooms.get(user.room_id)
                    if room:
                        room.users.pop(user.name, None)
                        if room.remote_control and room.controller_name == user.name:
                            room.controller_name = room.owner_name
                        await push_room_state(room)
                        await push_rooms_list_to_all()


# ═══════════════════════════════════════════════════════════════════════════════
# RICH DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def build_dashboard(local_ip: str) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="rooms", ratio=3),
        Layout(name="right", ratio=2),
    )
    layout["right"].split_column(
        Layout(name="users"),
        Layout(name="log"),
    )

    # ── Header ───────────────────────────────────────────────────────────────
    uptime = int(time.time() - state.start_time)
    h, m, s = uptime // 3600, (uptime % 3600) // 60, uptime % 60
    header_text = Text.assemble(
        ("🎬 ReelWatch Server v2", "bold magenta"),
        ("  │  ", "dim"),
        (f"ws://{local_ip}:{PORT}", "bold cyan"),
        ("  │  ", "dim"),
        (f"⏱ {h:02d}:{m:02d}:{s:02d}", "green"),
        ("  │  ", "dim"),
        (f"👥 {state.total_users} users", "yellow"),
        ("  │  ", "dim"),
        (f"🏠 {state.total_rooms} rooms", "blue"),
    )
    layout["header"].update(Panel(Align.center(header_text), style="bold", box=box.HORIZONTALS))

    # ── Rooms table ───────────────────────────────────────────────────────────
    rooms_table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
        expand=True,
        padding=(0, 1),
    )
    rooms_table.add_column("Room", style="yellow bold", min_width=12)
    rooms_table.add_column("Owner", style="green")
    rooms_table.add_column("👥", justify="center", width=4)
    rooms_table.add_column("Remote", justify="center", width=8)
    rooms_table.add_column("Controller", style="magenta")
    rooms_table.add_column("Current Reel", style="dim cyan", max_width=24)
    rooms_table.add_column("Users", style="white")

    if state.rooms:
        for room in state.rooms.values():
            remote_badge = Text("ON", style="bold green") if room.remote_control else Text("off", style="dim")
            controller = room.controller_name if room.remote_control else "—"
            user_names = ", ".join(room.users.keys()) or "—"
            reel = room.current_reel[:22] if room.current_reel else "—"
            rooms_table.add_row(
                room.room_id,
                room.owner_name,
                str(len(room.users)),
                remote_badge,
                controller,
                reel,
                user_names,
            )
    else:
        rooms_table.add_row("[dim]No rooms yet[/dim]", "", "", "", "", "", "")

    layout["rooms"].update(Panel(rooms_table, title="[bold cyan]🏠 Rooms[/bold cyan]", box=box.ROUNDED))

    # ── Users table ───────────────────────────────────────────────────────────
    users_table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold yellow",
        expand=True,
        padding=(0, 1),
    )
    users_table.add_column("User", style="bold white", min_width=10)
    users_table.add_column("Room", style="yellow")
    users_table.add_column("Watching", style="dim cyan", max_width=20)

    real_users = [u for u in state.connections.values() if u is not None]
    if real_users:
        for user in real_users:
            room_label = user.room_id or "[dim]lobby[/dim]"
            reel = user.current_reel[:18] if user.current_reel != "—" else "—"
            users_table.add_row(user.name, room_label, reel)
    else:
        users_table.add_row("[dim]No users[/dim]", "", "")

    layout["users"].update(Panel(users_table, title="[bold yellow]👥 Users[/bold yellow]", box=box.ROUNDED))

    # ── Log ───────────────────────────────────────────────────────────────────
    log_lines = state.log_lines[-10:]
    log_text = Text()
    for line in log_lines:
        log_text.append(line + "\n")

    layout["log"].update(Panel(log_text, title="[bold white]📋 Log[/bold white]", box=box.ROUNDED))

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_text = Text.assemble(
        ("  Ctrl+C to stop  ", "dim"),
        ("│", "dim"),
        (f"  Local: ws://{local_ip}:{PORT}  ", "cyan"),
        ("│", "dim"),
        ("  Localhost: ws://127.0.0.1:", "dim"),
        (str(PORT), "white"),
        ("  ", "dim"),
    )
    layout["footer"].update(Panel(Align.center(footer_text), box=box.HORIZONTALS, style="dim"))

    return layout


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    local_ip = get_local_ip()

    state.add_log(f"[bold green]Server started[/bold green] on [cyan]ws://{local_ip}:{PORT}[/cyan]")

    async def serve():
        async with websockets.serve(
            handle_connection,
            "0.0.0.0",
            PORT,
            ping_interval=20,
            ping_timeout=10,
        ):
            await asyncio.Future()

    server_task = asyncio.create_task(serve())

    with Live(build_dashboard(local_ip), refresh_per_second=4, console=console, screen=True) as live:
        while not server_task.done():
            live.update(build_dashboard(local_ip))
            await asyncio.sleep(0.25)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 ReelWatch Server stopped.[/bold red]")