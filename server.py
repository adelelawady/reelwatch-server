#!/usr/bin/env python3
"""
ReelWatch WebSocket Server
Run with: python server.py
"""

import asyncio
import json
import websockets
from websockets.server import WebSocketServerProtocol

# roomId → set of websocket connections
rooms: dict[str, set[WebSocketServerProtocol]] = {}

PORT = 3001


async def broadcast(room_id: str, msg: dict, skip: WebSocketServerProtocol):
    """Send a message to all clients in a room except the sender."""
    room = rooms.get(room_id)
    if not room:
        return
    payload = json.dumps(msg)
    dead = set()
    for client in room:
        if client is skip:
            continue
        try:
            await client.send(payload)
        except websockets.ConnectionClosed:
            dead.add(client)
    # Clean up any dead connections found during broadcast
    room -= dead


async def handle_connection(ws: WebSocketServerProtocol):
    room_id = None

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            # ── join ──────────────────────────────────────────────────────────
            if msg_type == "join":
                room_id = msg.get("room") or "default"
                if room_id not in rooms:
                    rooms[room_id] = set()
                rooms[room_id].add(ws)
                print(f"[{room_id}] joined — {len(rooms[room_id])} peer(s)")

            # ── url ───────────────────────────────────────────────────────────
            elif msg_type == "url":
                url = msg.get("url", "")
                parts = url.split("/reels/")
                reel = parts[1].replace("/", "") if len(parts) > 1 else url
                print(f"\r[{room_id}] reel → {reel:<40}", end="", flush=True)
                await broadcast(room_id, msg, ws)

            # ── comment ───────────────────────────────────────────────────────
            elif msg_type == "comment":
                print(f"[{room_id}] 💬 {msg.get('text', '')}")
                await broadcast(room_id, msg, ws)

            # ── reel_url ──────────────────────────────────────────────────────
            elif msg_type == "reel_url":
                url = msg.get("url", "")
                parts = url.split("/reels/")
                reel_id = parts[1].replace("/", "") if len(parts) > 1 else url
                print(f"\r[{room_id}] 📺 {reel_id:<40}", end="", flush=True)
                await broadcast(room_id, msg, ws)

            # ── reel_src ──────────────────────────────────────────────────────
            elif msg_type == "reel_src":
                print(f"\r[{room_id}] 📺 new reel src{'':<30}", end="", flush=True)
                await broadcast(room_id, msg, ws)

            # ── reel_index ────────────────────────────────────────────────────
            elif msg_type == "reel_index":
                print(f"\r[{room_id}] 📺 reel #{msg.get('index'):<30}", end="", flush=True)
                await broadcast(room_id, msg, ws)

    except websockets.ConnectionClosed:
        pass
    finally:
        # Clean up on disconnect
        if room_id and room_id in rooms:
            rooms[room_id].discard(ws)
            print(f"\n[{room_id}] left — {len(rooms[room_id])} peer(s)")


async def main():
    print("\n🎬 ReelWatch server running (Python)")
    print(f"   ws://YOUR_PC_IP:{PORT}")
    print("   Find your IP: run 'ipconfig' (Windows) or 'ifconfig' (Mac/Linux)\n")

    async with websockets.serve(handle_connection, "0.0.0.0", PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped.")