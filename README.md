# 🎬 ReelWatch

<div align="center">


<img width="200" height="200" alt="ReelWatch Logo" src="https://github.com/user-attachments/assets/da97ddc3-153f-4077-a666-b0de92902fc3" />

**Watch Instagram Reels together, in sync, in real time.**

> **⚠️ Important Note**: You'll need a **new Instagram account** to use ReelWatch. This ensures optimal performance and avoids conflicts with your main Instagram account.

**ReelWatch brings people together through shared entertainment.** Open Instagram together in real-time with live comments - watch funny reels, romantic moments, and viral content with your loved ones, no matter the distance.


🌐 **Try it now**: [reelwatch.adelelawady.org](https://reelwatch.adelelawady.org/)  | 🌐 **Server**: [reelwatch-server](https://github.com/adelelawady/reelwatch-server)


<img width="1858" height="927" alt="Screenshot 2026-03-23 220603" src="https://github.com/user-attachments/assets/28aa4fa4-70c6-453e-8e9a-706ea5095f67" />





# 🎬 ReelWatch Server — Python Setup Guide

A WebSocket server that syncs Instagram Reels watching across devices.
This is a Python port of the original Node.js `server.js`.

---

## 📋 Requirements

- Python **3.10 or newer** (uses `asyncio`)
- pip (comes bundled with Python)

---

## 🚀 Quick Start (Step by Step)

### Step 1 — Check your Python version

Open a terminal (Command Prompt / PowerShell on Windows, Terminal on Mac/Linux) and run:

```bash
python --version
```

You need `3.10+`. If you see `Python 2.x` try `python3 --version` instead and use `python3` for all commands below.

---

### Step 2 — Create the project folder

```bash
mkdir reelwatch-server
cd reelwatch-server
```

---

### Step 3 — Copy the server files

Place both files inside `reelwatch-server/`:

```
reelwatch-server/
├── server.py
└── requirements.txt
```

---

### Step 4 — Create a virtual environment (recommended)

A virtual environment keeps dependencies isolated from your system Python.

```bash
# Create the environment
python -m venv venv

# Activate it:
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac / Linux
source venv/bin/activate
```

You'll see `(venv)` appear at the start of your terminal prompt — that means it's active.

---

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs the `websockets` library (the only dependency).

---

### Step 6 — Find your local IP address

Other devices connect using your machine's local IP.

| OS | Command |
|----|---------|
| Windows | `ipconfig` → look for **IPv4 Address** under your Wi-Fi adapter |
| Mac | `ifconfig en0` → look for **inet** |
| Linux | `ip a` or `ifconfig` → look for **inet** under your active interface |

Example IP: `192.168.1.42`

---

### Step 7 — Run the server

```bash
python server.py
```

You should see:

```
🎬 ReelWatch server running (Python)
   ws://YOUR_PC_IP:3001
   Find your IP: run 'ipconfig' (Windows) or 'ifconfig' (Mac/Linux)
```

---

### Step 8 — Connect clients

In your extension or client, use:

```
ws://192.168.1.42:3001
```

Replace `192.168.1.42` with your actual IP from Step 6.

---

## 📡 WebSocket Message Protocol

The server handles these message types (same as the original Node.js version):

| `type` | Description | Fields |
|--------|-------------|--------|
| `join` | Join a sync room | `room` (optional, defaults to `"default"`) |
| `url` | Broadcast a reel URL | `url` |
| `comment` | Broadcast a comment | `text` |
| `reel_url` | Broadcast reel page URL | `url` |
| `reel_src` | Broadcast reel video src | — |
| `reel_index` | Broadcast reel position | `index` |

### Example messages (JSON)

```json
{ "type": "join", "room": "myroom" }
{ "type": "reel_url", "url": "https://www.instagram.com/reels/ABC123/" }
{ "type": "comment", "text": "lol this is funny" }
{ "type": "reel_index", "index": 3 }
```

---

## 🔁 Stopping and Restarting

To stop the server press `Ctrl + C` in the terminal.

To restart:
```bash
python server.py
```

---

## 🛠️ Troubleshooting

### Port already in use
```bash
# Find what's using port 3001
# Windows
netstat -ano | findstr :3001

# Mac/Linux
lsof -i :3001
```
Or change `PORT = 3001` at the top of `server.py` to another port like `3002`.

### Clients can't connect
- Make sure the server machine's **firewall** allows inbound connections on port 3001.
- Windows: Search "Windows Defender Firewall" → Advanced Settings → Inbound Rules → New Rule → Port 3001.
- All devices must be on the **same Wi-Fi network**.

### `websockets` not found after installing
Make sure your virtual environment is active (`(venv)` in your prompt), then re-run:
```bash
pip install -r requirements.txt
```

### Python version error
Upgrade Python from https://python.org/downloads — get 3.10 or newer.

---

## 📁 Project Structure

```
reelwatch-server/
├── server.py          ← Main server (this is the only file you need to run)
├── requirements.txt   ← Python dependencies
└── venv/              ← Virtual environment (created in Step 4, not committed to git)
```

---

## 🔄 Differences from the Node.js version

| Feature | Node.js | Python |
|---------|---------|--------|
| Runtime | `node server.js` | `python server.py` |
| WebSocket library | `ws` | `websockets` |
| Concurrency | Event loop (libuv) | `asyncio` event loop |
| Behavior | Identical | Identical |
| Port | 3001 | 3001 |

All message types and room behavior are exactly the same.
