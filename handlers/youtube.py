import asyncio
import os
import uuid

import yt_dlp
from aiogram import F, Router, types
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

router = Router()

DOWNLOAD_DIR = "downloads/youtube_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

cache = {}


def download_youtube(url: str, output_path: str, format_code: str) -> str:
    if format_code == "360p":
        ydl_format = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best"
    elif format_code == "720p":
        ydl_format = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
    elif format_code == "Audio":
        ydl_format = "bestaudio/best"
    else:
        ydl_format = "best"

    ydl_opts = {
        "format": ydl_format,
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
    }

    if format_code == "mp3":
        ydl_opts.update(
            {
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
            }
        )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if format_code == "mp3":
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename


@router.message(
    F.text.regexp(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/")
)
async def youtube_handler(message: Message):
    url = message.text.strip()
    video_id = uuid.uuid4().hex[:8]
    cache[video_id] = {"url": url}

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="360p", callback_data=f"yt:{video_id}:360p"
                ),
                InlineKeyboardButton(
                    text="720p", callback_data=f"yt:{video_id}:720p"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="MP3", callback_data=f"yt:{video_id}:mp3"
                ),
            ],
        ]
    )

    await message.answer("Выбери формат для скачивания:", reply_markup=kb)


@router.callback_query(F.data.startswith("yt:"))
async def youtube_callback(callback: CallbackQuery):
    try:
        _, video_id, fmt = callback.data.split(":")
        url = cache.get(video_id, {}).get("url")

        if not url:
            await callback.message.edit_text("Ссылка устарела, отправь снова.")
            return

        await callback.message.edit_text(f" Скачиваю в формате {fmt}...")

        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(
            None, download_youtube, url, DOWNLOAD_DIR, fmt
        )

        file = FSInputFile(filepath)

        if fmt == "mp3":
            await callback.message.answer_audio(
                file, caption="Скачано в @SaveTTasrobot"
            )
        else:
            await callback.message.answer_video(
                file, caption="Скачано в @SaveTTasrobot"
            )

        os.remove(filepath)

    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
