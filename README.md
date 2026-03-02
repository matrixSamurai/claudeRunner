# Claude Code Telegram Bot

Control Claude Code on your server from Telegram. Send instructions, get code changes applied, and see a live preview link — all from your phone.

---

## How It Works

```
You (Telegram) ──► Bot ──► Claude Code CLI ──► Your Repo
                                  │
                     Dev Server (Next.js) ──► Cloudflare Tunnel ──► Preview URL ──► You
```

---

## Setup (Step by Step)

### 1. Create a Telegram Bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** you receive

### 2. Get Your Telegram User ID

1. Message **@userinfobot** on Telegram
2. It will reply with your numeric user ID
3. Save it — you'll need it in the config

### 3. Install Dependencies on Your Server

```bash
# Python deps
pip3 install -r requirements.txt

# Cloudflare tunnel binary
# Option A — Download directly:
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Option B — via package manager (Debian/Ubuntu):
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

# Claude Code (if not already installed)
npm install -g @anthropic-ai/claude-code
```

### 4. Configure the Bot

```bash
cp .env.example .env
nano .env
```

Fill in:
- `TELEGRAM_BOT_TOKEN` — from @BotFather
- `ALLOWED_USER_IDS` — your Telegram user ID
- `FRONTEND_REPO_PATH` — absolute path to your Next.js repo
- `BACKEND_REPO_PATH` — absolute path to your backend repo
- `CLAUDE_BIN` — run `which claude` to find the path
- `CLOUDFLARED_BIN` — run `which cloudflared` to find the path

### 5. Load the .env and Run

```bash
# Load env vars and run
export $(cat .env | xargs) && python3 bot.py
```

### 6. (Optional) Run as a System Service

So the bot survives server reboots:

```bash
# Edit the service file with your paths
nano claude-bot.service

# Install it
sudo cp claude-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable claude-bot
sudo systemctl start claude-bot

# Check it's running
sudo systemctl status claude-bot

# View logs live
sudo journalctl -u claude-bot -f
```

---

## Usage

Once the bot is running, open Telegram and message your bot:

| What you send | What happens |
|---|---|
| `fix the login button alignment` | Claude edits frontend repo |
| `add a /health endpoint` | Claude edits backend repo |
| `/start` | Shows control panel with buttons |

### Buttons

- **🎨 Frontend** — Switch to frontend repo target
- **⚙️ Backend** — Switch to backend repo target
- **▶️ Start Preview** — Start Cloudflare tunnel, get public URL
- **⏹ Stop Preview** — Stop the tunnel
- **🔄 Restart Dev Server** — Restart Next.js dev server
- **📋 Status** — Show current tunnel URL and server status

---

## File Structure

```
claude-telegram-dev/
├── bot.py            # Main bot — Telegram handlers
├── config.py         # All settings (reads from .env)
├── claude_runner.py  # Runs `claude --print` and manages dev server
├── tunnel.py         # Starts/stops cloudflared tunnel
├── requirements.txt  # Python dependencies
├── .env.example      # Config template
├── claude-bot.service # systemd service file
└── README.md
```

---

## Security Notes

- Only users listed in `ALLOWED_USER_IDS` can control the bot
- Keep your `.env` file private (never commit it to git)
- Claude Code runs with the permissions of your server user
- The Cloudflare tunnel URL is public — don't expose sensitive data in your dev app

---

## Troubleshooting

**Bot doesn't respond:**
- Check `TELEGRAM_BOT_TOKEN` is correct
- Check your user ID is in `ALLOWED_USER_IDS`

**Claude command not found:**
- Run `which claude` on your server
- Set the full path in `CLAUDE_BIN` in your `.env`

**Tunnel URL not appearing:**
- Make sure `cloudflared` is installed: `cloudflared --version`
- Make sure your dev server is actually running on `FRONTEND_DEV_PORT`

**Dev server not starting:**
- Check `FRONTEND_REPO_PATH` is correct
- Make sure `npm install` has been run in that directory
- Check `FRONTEND_DEV_COMMAND` matches your `package.json` scripts
