import asyncio
import os
import logging
import yt_dlp
from aiogram import F, Router
from aiogram.types import FSInputFile, Message

router = Router()

DOWNLOAD_DIR = "downloads/instagram_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

INSTAGRAM_REGEX = r"(https?://)?(www\.)?(instagram\.com|instagr\.am)/(p|reel|reels|tv)/[A-Za-z0-9_-]+"


def download_instagram(url: str, output_path: str) -> list[str]:
    ydl_opts = {
        "format": "mp4",
        "outtmpl": os.path.join(output_path, "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }
    filepaths = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if "entries" in info:
            for entry in info["entries"]:
                filepaths.append(ydl.prepare_filename(entry))
        else:
            filepaths.append(ydl.prepare_filename(info))

    return filepaths


@router.message(F.text.regexp(INSTAGRAM_REGEX))
async def handle_instagram(message: Message):
    url = message.text.strip()
    status_message = await message.answer("Скачиваю Instagram...")

    try:
        loop = asyncio.get_event_loop()
        filepaths = await loop.run_in_executor(
            None, download_instagram, url, DOWNLOAD_DIR
        )

        for filepath in filepaths:
            if filepath.endswith(".mp4"):
                await message.answer_video(
                    FSInputFile(filepath), caption="Скачано в @SaveTTasrobot"
                )
            elif filepath.endswith((".jpg", ".jpeg", ".png")):
                await message.answer_photo(
                    FSInputFile(filepath), caption="Скачано в @SaveTTasrobot"
                )

            os.remove(filepath)

    except Exception as e:
        await message.answer(f"Ошибка при загрузке: {e}")
    finally:
        await status_message.delete()
