# 🎬 ReelWatch

<div align="center">

<img src="https://github.com/user-attachments/assets/da97ddc3-153f-4077-a666-b0de92902fc3" width="160" />

### 📡 Watch Instagram Reels Together — In Sync, In Real-Time

[![GitHub stars](https://img.shields.io/github/stars/adelelawady/reelwatch?style=for-the-badge)](https://github.com/adelelawady/reelwatch)
[![GitHub forks](https://img.shields.io/github/forks/adelelawady/reelwatch?style=for-the-badge)](https://github.com/adelelawady/reelwatch)
[![License](https://img.shields.io/github/license/adelelawady/reelwatch?style=for-the-badge)](https://github.com/adelelawady/reelwatch)
[![Repo size](https://img.shields.io/github/repo-size/adelelawady/reelwatch?style=for-the-badge)](https://github.com/adelelawady/reelwatch)
[![Last commit](https://img.shields.io/github/last-commit/adelelawady/reelwatch?style=for-the-badge)](https://github.com/adelelawady/reelwatch)
[![Issues](https://img.shields.io/github/issues/adelelawady/reelwatch?style=for-the-badge)](https://github.com/adelelawady/reelwatch/issues)

</div>

---

## 🚀 Overview

**ReelWatch** is a real-time synchronized Instagram Reels watching platform that allows multiple users to:

- 🎥 Watch reels together  
- 💬 Chat live while watching  
- 🎮 Control playback collaboratively or via a host  
- 🌍 Stay connected from anywhere  

> ⚠️ **Important:** Use a **secondary Instagram account** for best experience.

---

## ✨ Features

- 🔄 **Real-time sync** across all users in a room  
- 🏠 **Room system** with join/leave support  
- 🎮 **Remote control mode** (host controls playback)  
- 👥 **Multi-user sessions** with live presence tracking  
- 💬 **Live comments/chat system**  
- 📡 **WebSocket-based ultra-fast communication**  
- 🔁 **Reel position sync (index-based scrolling)**  
- 🔗 **URL & video source synchronization**

---

## 🧠 How It Works

ReelWatch uses a **WebSocket-based architecture** to maintain real-time synchronization:

1. Client connects to server via WebSocket  
2. User registers with a unique name  
3. User creates or joins a room  
4. Reel interactions are broadcast in real-time  
5. Server enforces sync rules (controller / shared mode)

### 🔄 Sync Modes

| Mode | Behavior |
|------|--------|
| `remote_control: true` | Only controller updates sync |
| `remote_control: false` | Everyone controls sync |

---

## 🛠 Tech Stack

### Frontend
- ⚛️ React Native / Expo
- 🌐 WebView (Instagram embedding)

### Backend
- 🐍 Python (asyncio)
- 🔌 websockets

### Infrastructure
- 🌍 WebSocket Protocol
- ⚡ Real-time event broadcasting

---

## 📦 Installation

### 🔧 Server Setup (Python)

```bash
git clone https://github.com/adelelawady/reelwatch-server.git
cd reelwatch-server
```

## 1 Create virtual environment
```
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```
## 2. Install dependencies
```
pip install -r requirements.txt
```


## 3. Run server
```
python server.py
```


### 🚀 Usage
## Connect to server

```
ws://YOUR_IP:3001
```

## Example Flow
```
register → create_room → join → sync reels → chat → transfer control
```


### 📡 API Reference (WebSocket)


## 🔐 Register
```
{ "type": "register", "name": "Alice" }
```
## 🏠 Room Management
```
{ "type": "create_room", "room": "movie-night", "remote_control": true }
{ "type": "join", "room": "movie-night" }
{ "type": "leave" }
{ "type": "delete_room", "room": "movie-night" }
```
## 🎮 Control
```
{ "type": "transfer_remote", "to": "Bob" }
```
## 🎥 Reel Sync
```
{ "type": "reel_url", "url": "https://instagram.com/reels/ABC123/" }
{ "type": "reel_index", "index": 3 }
```
## 💬 Chat
```
{ "type": "comment", "text": "This is hilarious 😂" }
```
## ❌ Error Example
```
{ "type": "error", "code": "NAME_TAKEN", "msg": "Name already used" }
```
## 📂 Project Structure
```
reelwatch/
├── app/                  # Mobile app (Expo)
├── components/           # UI components
├── server/               # Backend server (Python)
│   ├── server.py
│   └── requirements.txt
├── assets/               # Images & icons
├── README.md
```

## 🖼 Screenshots
1️⃣ Main Interface

<img src="https://github.com/user-attachments/assets/28aa4fa4-70c6-453e-8e9a-706ea5095f67" />
2️⃣ APP Experience
<img width="447" height="892" alt="Screenshot 2026-03-24 064130" src="https://github.com/user-attachments/assets/d0ccec33-adc3-4b34-bb7b-9489d30c28f7" />


### 🧪 Development

## Run in development mode

# Backend

```
python server.py
```

# Frontend (Expo)

```
npx expo start
```

### 🤝 Contributing

Contributions are welcome!
```
Steps:
Fork the repo
Create a feature branch
Commit your changes
Push and open a PR
git checkout -b feature/amazing-feature
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```
### 📜 License

This project is licensed under the MIT License.

### ⭐ Support

If you like this project:

⭐ Star the repo
🐛 Report issues
💡 Suggest features
📢 Share it with others
🌐 Live Demo

👉 https://reelwatch.adelelawady.org/
```
<div align="center">

Built with ❤️ by Adel Alawady

</div>
```

