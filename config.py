"""
Configuration for Claude Code Telegram Bot.
Edit this file or set environment variables.
"""

import os
from pathlib import Path


class Config:
    # ─── REQUIRED ────────────────────────────────────────────────────────────

    # Your Telegram Bot Token from @BotFather
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

    # Comma-separated Telegram user IDs allowed to control the bot
    # Get your ID by messaging @userinfobot on Telegram
    ALLOWED_USER_IDS: list[str] = os.getenv(
        "ALLOWED_USER_IDS", "YOUR_TELEGRAM_USER_ID"
    ).split(",")

    # ─── REPO PATHS ──────────────────────────────────────────────────────────

    # Absolute path to your Next.js frontend repo on the server
    FRONTEND_REPO_PATH: str = os.getenv(
        "FRONTEND_REPO_PATH", "/home/user/projects/my-frontend"
    )

    # Absolute path to your backend repo on the server
    BACKEND_REPO_PATH: str = os.getenv(
        "BACKEND_REPO_PATH", "/home/user/projects/my-backend"
    )

    # ─── DEV SERVER ──────────────────────────────────────────────────────────

    # Command to start the Next.js frontend dev server
    FRONTEND_DEV_COMMAND: str = os.getenv("FRONTEND_DEV_COMMAND", "npm run dev")

    # Port your Next.js dev server runs on
    FRONTEND_DEV_PORT: int = int(os.getenv("FRONTEND_DEV_PORT", "3000"))

    # Command to start the backend dev server
    BACKEND_DEV_COMMAND: str = os.getenv("BACKEND_DEV_COMMAND", "npm run dev")

    # Port your backend dev server runs on (used for status checks)
    BACKEND_DEV_PORT: int = int(os.getenv("BACKEND_DEV_PORT", "8000"))

    # ─── CLAUDE CODE ─────────────────────────────────────────────────────────

    # Path to claude binary (run `which claude` on your server)
    CLAUDE_BIN: str = os.getenv("CLAUDE_BIN", "claude")

    # Max seconds to wait for Claude to finish a task
    CLAUDE_TIMEOUT: int = int(os.getenv("CLAUDE_TIMEOUT", "300"))

    # Tools Claude is allowed to use
    CLAUDE_ALLOWED_TOOLS: str = os.getenv(
        "CLAUDE_ALLOWED_TOOLS", "Edit,Read,Write,Bash,Glob,Grep"
    )

    # ─── CLOUDFLARE TUNNEL ───────────────────────────────────────────────────

    # Which port to expose via Cloudflare Tunnel (usually your frontend port)
    TUNNEL_PORT: int = int(os.getenv("TUNNEL_PORT", "3000"))

    # Path to cloudflared binary (run `which cloudflared` on your server)
    CLOUDFLARED_BIN: str = os.getenv("CLOUDFLARED_BIN", "cloudflared")
