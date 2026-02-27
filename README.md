# 🎵 MusikBOT

A Discord music bot that plays audio from **YouTube** (and more) — powered by **Lavalink** and slash commands.

![Node.js](https://img.shields.io/badge/Node.js-22+-339933?logo=node.js&logoColor=white)
![discord.js](https://img.shields.io/badge/discord.js-14-5865F2?logo=discord&logoColor=white)
![Lavalink](https://img.shields.io/badge/Lavalink-4-orange)

---

## ✨ Features

- 🎶 **Play from YouTube** — paste a URL or search by name
- 🔍 **Smart search** — just type a song name and the bot finds it
- 📋 **Queue system** — queue multiple tracks, skip, pause, resume
- 🔁 **Loop mode** — repeat the current track
- 🔊 **Volume control** — adjustable 1–100%
- ⏱️ **Auto-disconnect** — leaves voice after 2 min of inactivity

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/play <query>` | Play a track (YouTube URL or search) |
| `/skip` | Skip the current track |
| `/queue` | Show the queue |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/stop` | Stop, clear queue, and disconnect |
| `/nowplaying` | Show the current track |
| `/volume <1-100>` | Set volume |
| `/loop` | Toggle loop for the current track |

---

## 🚀 Setup

### Prerequisites

- **Node.js 20+** (22 recommended)
- **Docker** (for Lavalink)

### 1. Clone & Install

```bash
cd MusikBOT
npm install
```

### 2. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** → name it **MusikBOT**
3. Go to **Bot** → click **Reset Token** → copy your token
4. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Connect`, `Speak`, `Send Messages`, `Embed Links`
5. Use the generated URL to invite the bot to your server

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your Discord bot token:

```env
DISCORD_TOKEN=your_discord_bot_token_here
```

The Lavalink defaults (`localhost:2333`, `youshallnotpass`) will work out of the box with the included Docker Compose setup.

### 4. Start Lavalink

```bash
docker compose up -d
```

This starts the Lavalink audio server with the **youtube-source** plugin.

#### YouTube OAuth (recommended)

On first launch, check the Lavalink logs:

```bash
docker compose logs -f lavalink
```

Look for a line like:
```
To give the minimum access, **only** select the **Send email** scope.
Visit the following URL: https://www.google.com/device ...
```

Follow the URL, sign in with a Google account, and authorize. Lavalink will remember the token automatically.

### 5. Run the Bot

```bash
node src/bot.js
```

You should see:
```
[Shoukaku] Node "main" connected
Logged in as MusikBOT#1234 (ID: ...)
Connected to 1 guild(s)
Synced 9 slash command(s)
```

---

## 📁 Project Structure

```
MusikBOT/
├── .env.example             # Environment template
├── .gitignore
├── package.json
├── docker-compose.yml       # Lavalink container
├── README.md
├── lavalink/
│   └── application.yml      # Lavalink server config
└── src/
    ├── bot.js               # Entry point (discord.js + Shoukaku)
    ├── queue.js              # Per-guild queue manager
    ├── embeds.js             # Embed builders & helpers
    └── commands/
        ├── play.js
        ├── skip.js
        ├── queue.js
        ├── pause.js
        ├── resume.js
        ├── stop.js
        ├── nowplaying.js
        ├── volume.js
        └── loop.js
```

## 📝 Notes

- **Lavalink** handles all audio extraction and streaming — no FFmpeg needed on the bot side.
- Slash commands may take up to an hour to appear globally after first sync. For instant testing, consider guild-specific sync.
- The youtube-source plugin supports multiple InnerTube clients and falls through them automatically if one is blocked.

---

## 📄 License

MIT — do whatever you want with it. 🎶
