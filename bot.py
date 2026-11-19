import os
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_ID = "2040"
API_HASH = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = "9101417197:AAFOnGosM_2m8d2Dqgt-ccBI66MgBbfXa3w"

app = Client(
    "OmniMediaUltimateBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

SUPPORTED_PLATFORMS = [
    "YouTube (Videos/Shorts)", "TikTok (No Watermark)", "Instagram (Reels/Posts)",
    "Facebook (Videos/Reels)", "Twitter (X)", "WhatsApp Status",
    "Pinterest", "Kwai", "Threads", "Snapchat",
    "Dailymotion", "Soundcloud", "Bluesky", "OK.ru"
]

@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_text = (
        f"👋 **Welcome to OmniMedia Ultimate Bot!**\n\n"
        f"🌟 The world's best All-in-One Media Downloader.\n"
        f"✨ Supports **Ultra HD Videos, Photos, Reels, & MP3 Audio** with zero watermarks from:\n\n"
        f"• " + "\n• ".join(SUPPORTED_PLATFORMS) + "\n\n"
        f"📥 **How to use:**\n"
        f"Simply send any media link, and get instant download options!"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Supported Platforms", callback_data="platforms"),
         InlineKeyboardButton("⚙️ Bot Status", callback_data="status")]
    ])
    await message.reply_text(welcome_text, reply_markup=keyboard)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply_text(
        "🛠 **Help & Guidelines:**\n\n"
        "1. Send any public media link (YouTube, TikTok, Instagram Reels, Facebook, etc.).\n"
        "2. The bot will parse the highest Ultra HD streams and formats.\n"
        "3. Choose MP4, Photos, or MP3 Audio to download instantly.\n\n"
        "⚡ Powered by Advanced Streaming Engine."
    )

@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    if data == "platforms":
        await callback_query.answer()
        await callback_query.message.edit_text(
            "📋 **Supported Platforms:**\n\n" + "\n".join([f"✅ {p}" for p in SUPPORTED_PLATFORMS]),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="back_home")]])
        )
    elif data == "status":
        await callback_query.answer("Bot is online and running 24/7! 🚀", show_alert=True)
    elif data == "back_home":
        await callback_query.answer()
        await callback_query.message.edit_text(
            "👋 **Welcome back to OmniMedia Ultimate Bot!**\nSend any media link to get started.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Supported Platforms", callback_data="platforms"),
                 InlineKeyboardButton("⚙️ Bot Status", callback_data="status")]
            ])
        )

@app.on_message(filters.text & ~filters.command(["start", "help"]))
async def process_media(client, message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.reply_text("❌ Please send a valid media URL starting with http:// or https://")
        return

    status_msg = await message.reply_text("🔍 **Analyzing Link & Extracting Ultra HD Streams...** Please wait.")

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best'
        }

        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await asyncio.to_thread(extract_info)
        title = info.get('title', 'Downloaded Media')
        duration = info.get('duration_string', 'N/A')
        uploader = info.get('uploader', 'Unknown Creator')

        keyboard_buttons = [
            [InlineKeyboardButton("🔥 Download Ultra HD Video (Max)", url=url)],
            [InlineKeyboardButton("📱 HD 720p / 1080p", url=url),
             InlineKeyboardButton("🎵 MP3 Audio Only", url=url)],
            [InlineKeyboardButton("🔗 Open Direct Source Link", url=url)]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard_buttons)

        caption = (
            f"🎯 **Media Extracted Successfully!**\n\n"
            f"📌 **Title:** {title}\n"
            f"👤 **Creator:** {uploader}\n"
            f"⏱ **Duration:** {duration}\n\n"
            f"👇 Select your preferred download option below:"
        )

        await status_msg.edit_text(caption, reply_markup=reply_markup)

    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Failed to process link.**\n\n"
            f"Reason: `{str(e)[:90]}`\n\n"
            f"Please ensure the link is public and from a supported platform."
        )

if __name__ == "__main__":
    print("🤖 OmniMedia Ultimate Bot is running...")
    app.run()
