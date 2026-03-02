#!/usr/bin/env python3
"""
Claude Code Telegram Bot
Controls Claude Code on your server via Telegram messages.
Supports frontend (Next.js) and backend repo management with live preview.
"""

import os
import asyncio
import subprocess
import logging
import signal
import sys
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from config import Config
from tunnel import TunnelManager
from claude_runner import ClaudeRunner

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

tunnel_manager = TunnelManager()
claude_runner = ClaudeRunner()

# Track active target repo per chat
active_targets: dict[int, str] = {}  # chat_id -> "frontend" | "backend"


def get_target(chat_id: int) -> str:
    return active_targets.get(chat_id, "frontend")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🎨 Frontend", callback_data="target_frontend"),
            InlineKeyboardButton("⚙️ Backend", callback_data="target_backend"),
        ],
        [
            InlineKeyboardButton("▶️ Start Preview", callback_data="start_preview"),
            InlineKeyboardButton("⏹ Stop Preview", callback_data="stop_preview"),
        ],
        [
            InlineKeyboardButton("📋 Status", callback_data="status"),
            InlineKeyboardButton("🔄 Restart Dev Server", callback_data="restart_dev"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *Claude Code Bot* is ready!\n\n"
        "Just send me any instruction and I'll run it through Claude Code.\n\n"
        "*Examples:*\n"
        "• `fix the login button alignment`\n"
        "• `add a dark mode toggle to the navbar`\n"
        "• `add a /health endpoint to the backend`\n\n"
        "Use the buttons below to switch repos or manage the preview.",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "target_frontend":
        active_targets[chat_id] = "frontend"
        await query.edit_message_text(
            "✅ Target switched to *Frontend* repo.\nSend me your instruction!",
            parse_mode="Markdown",
        )

    elif query.data == "target_backend":
        active_targets[chat_id] = "backend"
        await query.edit_message_text(
            "✅ Target switched to *Backend* repo.\nSend me your instruction!",
            parse_mode="Markdown",
        )

    elif query.data == "start_preview":
        msg = await query.edit_message_text("🚀 Starting preview tunnel...")
        url = await tunnel_manager.start()
        if url:
            await msg.edit_text(
                f"✅ Preview is live!\n\n🔗 {url}\n\nDev server is running on the frontend repo.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Open Preview", url=url)]]
                ),
            )
        else:
            await msg.edit_text("❌ Failed to start tunnel. Check logs.")

    elif query.data == "stop_preview":
        await tunnel_manager.stop()
        await query.edit_message_text("⏹ Preview tunnel stopped.")

    elif query.data == "restart_dev":
        msg = await query.edit_message_text("🔄 Restarting dev server...")
        success = await claude_runner.restart_dev_server()
        if success:
            url = tunnel_manager.current_url
            text = "✅ Dev server restarted!"
            if url:
                text += f"\n\n🔗 {url}"
            await msg.edit_text(text)
        else:
            await msg.edit_text("❌ Failed to restart dev server. Check logs.")

    elif query.data == "status":
        target = get_target(chat_id)
        tunnel_url = tunnel_manager.current_url or "Not running"
        dev_running = await claude_runner.is_dev_server_running()
        status_text = (
            f"📊 *Status*\n\n"
            f"🎯 Active repo: `{target}`\n"
            f"🌐 Tunnel: `{tunnel_url}`\n"
            f"💻 Dev server: {'✅ Running' if dev_running else '❌ Stopped'}\n"
        )
        await query.edit_message_text(status_text, parse_mode="Markdown")


async def handle_instruction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle a natural language instruction from the user."""
    if str(update.effective_user.id) not in Config.ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    instruction = update.message.text.strip()
    chat_id = update.effective_chat.id
    target = get_target(chat_id)

    repo_path = (
        Config.FRONTEND_REPO_PATH if target == "frontend" else Config.BACKEND_REPO_PATH
    )
    repo_label = "Frontend 🎨" if target == "frontend" else "Backend ⚙️"

    status_msg = await update.message.reply_text(
        f"⏳ Running on *{repo_label}* repo...\n\n`{instruction}`",
        parse_mode="Markdown",
    )

    try:
        result = await claude_runner.run(instruction, repo_path)

        preview_url = tunnel_manager.current_url
        reply = f"✅ *Done!* ({repo_label})\n\n"

        if result.get("output"):
            output = result["output"][:1500]  # Telegram limit
            reply += f"```\n{output}\n```\n"

        if preview_url and target == "frontend":
            reply += f"\n🔗 [Open Preview]({preview_url})"

        keyboard = [
            [InlineKeyboardButton("🔄 Restart Dev Server", callback_data="restart_dev")],
        ]
        if preview_url:
            keyboard.append([InlineKeyboardButton("🔗 Open Preview", url=preview_url)])

        await status_msg.edit_text(
            reply,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.exception("Error running Claude instruction")
        await status_msg.edit_text(
            f"❌ *Error:*\n```\n{str(e)[:500]}\n```",
            parse_mode="Markdown",
        )


async def post_init(application: Application):
    """Start tunnel and dev server on bot startup."""
    logger.info("Starting dev server and tunnel...")
    await claude_runner.start_dev_server()
    url = await tunnel_manager.start()
    if url:
        logger.info(f"Preview available at: {url}")


def main():
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instruction)
    )

    logger.info("Bot started. Listening for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
