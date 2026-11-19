import imageio_ffmpeg
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
import os
import logging
import asyncio
import glob
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_ID = int(os.getenv("API_ID", "2040"))
API_HASH = os.getenv("API_HASH", "b18441a1ff607e10a989891a5462e627")
BOT_TOKEN = "9101417197:AAFOnGosM_2m8d2Dqgt-ccBI66MgBbfXa3w"

app = Client(
    "OmniMediaUltimateBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Temporary store for user links: {user_id: url}
USER_LINKS = {}
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def cleanup_user_files(prefix: str):
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, f"{prefix}*")):
        try:
            os.remove(f)
        except Exception:
            pass


@app.on_message(filters.command("start"))
async def start_command(client, message):
    text = (
        "👋 **Welcome to OmniMedia Ultimate Bot!**\n\n"
        "Send any public link from **YouTube, TikTok, Instagram, Facebook, X (Twitter), Pinterest, Threads, Dailymotion, SoundCloud**, etc.\n\n"
        "Choose **Best Video (MP4)** or **MP3 Audio** after sending the link."
    )
    await message.reply_text(text)


@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_link(client, message):
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.reply_text("❌ Please send a valid URL starting with http:// or https://")
        return

    status = await message.reply_text("🔍 **Checking link info...**")

    try:
        def get_info():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await asyncio.to_thread(get_info)
        title = info.get("title") or "Media"
        duration = info.get("duration_string") or "N/A"

        USER_LINKS[message.from_user.id] = url

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Download Best Video (MP4)", callback_data="dl_video")],
            [InlineKeyboardButton("🎵 Download Audio (MP3)", callback_data="dl_mp3")]
        ])

        await status.edit_text(
            f"📌 **Title:** {title[:120]}\n"
            f"⏱ **Duration:** {duration}\n\n"
            f"Select format to download:",
            reply_markup=buttons
        )

    except Exception as e:
        logging.exception("Info extraction error")
        await status.edit_text(f"❌ **Could not read this link.**\n`{str(e)[:150]}`")


@app.on_callback_query(filters.regex("^dl_(video|mp3)$"))
async def download_callback(client, callback_query: CallbackQuery):
    mode = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    url = USER_LINKS.get(user_id)

    if not url:
        await callback_query.answer("Link expired. Please send the link again.", show_alert=True)
        return

    await callback_query.answer("Starting download...")
    msg = await callback_query.message.edit_text(
        "⬇️ **Downloading media to server...** Please wait."
    )

    prefix = f"{user_id}_{callback_query.id}"
    out_template = os.path.join(DOWNLOAD_DIR, f"{prefix}.%(ext)s")

    try:
        if mode == "video":
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "ffmpeg_location": FFMPEG_PATH,
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": out_template,
            }
        else:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "ffmpeg_location": FFMPEG_PATH,
                "format": "bestaudio/best",
                "outtmpl": out_template,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

        def run_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)

        await asyncio.to_thread(run_download)

        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{prefix}*"))
        if not files:
            raise FileNotFoundError("Downloaded file not found.")

        file_path = max(files, key=os.path.getsize)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        # Telegram Bot API standard upload limit is ~50MB unless using a local Bot API server
        if file_size_mb > 49.5:
            await msg.edit_text(
                f"⚠️ **File is too large for standard Telegram Bot upload ({file_size_mb:.1f} MB).**\n"
                f"Standard Telegram bots are limited to 50 MB per file."
            )
            cleanup_user_files(prefix)
            return

        await msg.edit_text("⬆️ **Uploading to Telegram...**")

        if mode == "video":
            await client.send_video(
                chat_id=callback_query.message.chat.id,
                video=file_path,
                caption="✅ Downloaded with OmniMedia Bot",
                supports_streaming=True
            )
        else:
            await client.send_audio(
                chat_id=callback_query.message.chat.id,
                audio=file_path,
                caption="✅ MP3 Audio"
            )

        await msg.delete()

    except Exception as e:
        logging.exception("Download/Upload error")
        await msg.edit_text(f"❌ **Download failed:**\n`{str(e)[:180]}`")
    finally:
        cleanup_user_files(prefix)


if __name__ == "__main__":
    print("🤖 OmniMedia Bot started...")
    app.run()
