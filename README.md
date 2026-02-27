# 🎵 MusikBOT

A Discord music bot that plays audio from **YouTube** or by **search query** — powered by slash commands.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.3+-5865F2?logo=discord&logoColor=white)

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

- **Python 3.10+**
- **FFmpeg** installed and in your `PATH`
  ```bash
  # Ubuntu / Debian
  sudo apt install ffmpeg

  # Arch
  sudo pacman -S ffmpeg

  # macOS
  brew install ffmpeg
  ```

### 1. Clone & Install

```bash
cd MusikBOT
python -m venv .venv
source .venv/bin/activate    # Linux / macOS
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt
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

### 4. Set Up YouTube Authentication

YouTube blocks automated requests. The recommended fix is the **PO Token plugin**, which generates authentication tokens automatically.

#### Option A — Docker (easiest, recommended)

```bash
docker run -d --name bgutil-provider --restart unless-stopped -p 4416:4416 brainicism/bgutil-ytdlp-pot-provider
```

That's it — the plugin (already in `requirements.txt`) will connect to the server on `127.0.0.1:4416` automatically.

#### Option B — Node.js (no Docker)

```bash
# Requires Node.js >= 20
git clone --single-branch --branch 1.2.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
cd bgutil-ytdlp-pot-provider/server/
npm ci && npx tsc
node build/main.js          # runs on port 4416
```

#### Option C — Cookies (fallback, expires periodically)

Export cookies from your browser using the [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension and place `cookies.txt` in the project root. See `.env.example` for details.

### 5. Run the Bot

```bash
python bot.py
```

You should see:
```
2026-02-27 04:00:00 │ musikbot              │ INFO     │ Logged in as MusikBOT#1234 (ID: ...)
2026-02-27 04:00:00 │ musikbot              │ INFO     │ Connected to 1 guild(s)
2026-02-27 04:00:00 │ musikbot              │ INFO     │ Synced 9 slash command(s)
```

---

## 📁 Project Structure

```
MusikBOT/
├── .env.example        # Environment template
├── .gitignore
├── requirements.txt
├── README.md
├── bot.py              # Entry point
├── cogs/
│   └── music.py        # Music slash commands
└── utils/
    └── music_sources.py # YouTube search & extraction
```

## 📝 Notes

- The bot requires the **FFmpeg** binary to transcode audio for Discord voice.
- Slash commands may take up to an hour to appear globally after first sync. For instant testing, consider guild-specific sync.

---

## 📄 License

MIT — do whatever you want with it. 🎶
