# 📡 ReelWatch Server v2 — WebSocket Protocol Reference

All messages are JSON. Client → Server and Server → Client.

---

## Client → Server Messages

### 1. Register (must be first message)
```json
{ "type": "register", "name": "Alice" }
```
**Response:** `registered` or `error` (NAME_TAKEN / NAME_REQUIRED)

---

### 2. Create Room
```json
{ "type": "create_room", "room": "movie-night", "remote_control": true }
```
- `remote_control: true` → only the controller can push reel changes to others
- `remote_control: false` → anyone's scroll syncs everyone (original behavior)

**Response:** `room_created` + `rooms_list` broadcast to all

---

### 3. Delete Room (owner only)
```json
{ "type": "delete_room", "room": "movie-night" }
```
**Response:** `room_deleted` broadcast to room members + `rooms_list` to all

---

### 4. Join Room
```json
{ "type": "join", "room": "movie-night" }
```
**Response:** `joined` + `room_state` to room + `rooms_list` to all

---

### 5. Leave Room
```json
{ "type": "leave" }
```

---

### 6. List Rooms
```json
{ "type": "list_rooms" }
```
**Response:** `rooms_list` to you

---

### 7. Transfer Remote (controller only)
```json
{ "type": "transfer_remote", "to": "Bob" }
```
**Response:** `remote_transferred` broadcast to room + `room_state`

---

### 8. Reel Updates (synced to room)
```json
{ "type": "reel_url",   "url": "https://instagram.com/reels/ABC123/" }
{ "type": "url",        "url": "https://instagram.com/reels/ABC123/" }
{ "type": "reel_src"  }
{ "type": "reel_index", "index": 3 }
```
⚠️ If room has `remote_control: true`, only the current controller's updates are broadcast.

---

### 9. Comment
```json
{ "type": "comment", "text": "lol this is so good" }
```
Broadcast to room with sender's name attached.

---

## Server → Client Messages

### registered
```json
{ "type": "registered", "name": "Alice" }
```

### rooms_list
```json
{
  "type": "rooms_list",
  "rooms": [
    {
      "id": "movie-night",
      "owner": "Alice",
      "remote_control": true,
      "controller": "Alice",
      "users": ["Alice", "Bob"],
      "user_count": 2,
      "current_reel": "ABC123xyz"
    }
  ]
}
```
Sent on connect and whenever rooms change.

### room_state
```json
{
  "type": "room_state",
  "room": {
    "id": "movie-night",
    "owner": "Alice",
    "remote_control": true,
    "controller": "Bob",
    "users": ["Alice", "Bob", "Charlie"],
    "user_count": 3,
    "current_reel": "ABC123xyz"
  }
}
```
Sent to all room members when state changes.

### joined
```json
{ "type": "joined", "room": "movie-night" }
```

### room_created
```json
{ "type": "room_created", "room": "movie-night" }
```

### room_deleted
```json
{ "type": "room_deleted", "room": "movie-night", "reason": "Owner deleted the room." }
```

### remote_transferred
```json
{ "type": "remote_transferred", "from": "Alice", "to": "Bob", "room": "movie-night" }
```

### comment (broadcast)
```json
{ "type": "comment", "text": "haha", "from": "Bob" }
```

### error
```json
{ "type": "error", "code": "NAME_TAKEN", "msg": "Name 'Alice' is already taken." }
```

**Error codes:**
| Code | Meaning |
|------|---------|
| `NAME_REQUIRED` | Empty name on register |
| `NAME_TAKEN` | Username already online |
| `ROOM_ID_REQUIRED` | Empty room ID |
| `ROOM_EXISTS` | Room ID already taken |
| `ROOM_NOT_FOUND` | Room doesn't exist |
| `NOT_OWNER` | Only owner can delete |
| `NOT_REGISTERED` | Message sent before register |
| `NO_REMOTE` | Room has no remote control |
| `NOT_CONTROLLER` | You don't hold the remote |
| `USER_NOT_IN_ROOM` | Transfer target not in room |

---

## Typical Client Flow

```
Client                          Server
  │── register { name }  ──────→│
  │←── registered         ──────│
  │←── rooms_list         ──────│
  │
  │── create_room { room, remote_control } →│
  │←── room_created        ──────│
  │←── rooms_list (all)   ──────│
  │
  │── join { room }  ──────────→│
  │←── joined              ──────│
  │←── room_state          ──────│
  │
  │── reel_url { url } ─────────→│  (broadcast to room if controller)
  │── comment { text } ─────────→│  (broadcast to room)
  │
  │── transfer_remote { to } ───→│
  │←── remote_transferred (room) │
  │←── room_state (room)   ──────│
  │
  │── delete_room { room } ─────→│
  │←── rooms_list (all)   ──────│
```