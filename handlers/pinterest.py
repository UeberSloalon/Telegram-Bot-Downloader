import asyncio
import re
import uuid
from pathlib import Path

import requests
import yt_dlp
from aiogram import F, Router, types
from aiogram.types import (FSInputFile, InlineQuery, InlineQueryResultArticle,
                           InputTextMessageContent, Message)

router = Router()


async def extract_video_url(page_url: str) -> str:
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL({"quiet": True}).extract_info(
                page_url, download=False
            ),
        )

        if "url" in info:
            return info["url"]
        elif "entries" in info and info["entries"]:
            return info["entries"][0].get("url")
    except Exception as e:
        print(f"[yt-dlp fail] {e}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36",
    }

    response = await asyncio.to_thread(
        lambda: requests.get(page_url, headers=headers, timeout=15)
    )

    if response.status_code != 200:
        raise Exception(f"Ошибка доступа к странице: {response.status_code}")

    html_content = response.text

    patterns = [
        r'"videos":\s*{.*?"url"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
        r'<meta property="og:video" content="(https?://[^"]+\.mp4[^"]*)"',
        r'<video[^>]+src="(https?://[^"]+\.mp4[^"]*)"',
        r'<source[^>]+src="(https?://[^"]+\.mp4[^"]*)"',
        r'(https?://[^"]+\.mp4[^"]*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            return match.group(1).replace("\\/", "/")

    raise Exception("Видео URL не найден в коде страницы")


async def send_pinterest_video(message: Message, page_url: str):
    try:
        video_url = await extract_video_url(page_url)

        try:

            await message.answer_video(
                video=video_url, caption="Cкачано в @SaveTTasrobot"
            )
            return
        except Exception as e:
            print(f"Прямая загрузка не сработала: {e}, качаю файл...")

        temp_dir = Path("downloads/pinterest_videos")
        temp_dir.mkdir(exist_ok=True)
        filepath = temp_dir / f"pinterest_{uuid.uuid4().hex}.mp4"

        video_response = await asyncio.to_thread(
            lambda: requests.get(video_url, stream=True, timeout=30)
        )
        if video_response.status_code != 200:
            raise Exception(
                f"Ошибка скачивания видео: {video_response.status_code}"
            )

        with open(filepath, "wb") as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        await message.answer_video(
            video=FSInputFile(filepath), caption="Скачано в @SaveTTasrobot"
        )
        filepath.unlink()

    except Exception as e:
        error_msg = str(e)
        if "Видео URL не найден" in error_msg:
            error_msg = (
                "Не удалось найти видео в этом пине. Возможно:\n"
                "• Это изображение, а не видео\n"
                "• Видео недоступно\n"
                "• Ссылка неверная"
            )
        await message.answer(error_msg)
        print(f"Pinterest error: {e}")


@router.inline_query()
async def pinterest_inline(query: InlineQuery):
    text = query.query.strip()

    if not text or ("pinterest" not in text and "pin.it" not in text):
        return

    try:
        video_url = await extract_video_url(text)

        result = types.InlineQueryResultVideo(
            id=str(uuid.uuid4()),
            video_url=video_url,
            mime_type="video/mp4",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/0/08/Pinterest-logo.png",
            title="🎬 Видео с Pinterest",
            caption="Cкачано в @SaveTTasrobot",
        )

        await query.answer([result], cache_time=0)

    except Exception as e:
        error_result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Ошибка",
            input_message_content=InputTextMessageContent(
                message_text=f"Не удалось скачать видео: {e}"
            ),
        )
        await query.answer([error_result], cache_time=0)


@router.message(F.text.startswith("https://pin.it/"))
async def handle_pinit_link(message: Message):
    short_url = message.text.strip()
    processing_msg = await message.answer("Распознаю короткую ссылку...")

    try:
        response = await asyncio.to_thread(
            lambda: requests.head(short_url, allow_redirects=True, timeout=10)
        )
        final_url = response.url

        if "/pin/" not in final_url:
            await processing_msg.edit_text("Это не ссылка на Pinterest pin!")
            return

        await processing_msg.edit_text("Скачиваю Pinterest видео...")
        await send_pinterest_video(message, final_url)
        await processing_msg.delete()

    except Exception as e:
        await processing_msg.edit_text(f"Ошибка при обработке ссылки: {e}")


@router.message(F.text.regexp(r"^https?://(www\.|ru\.)?pinterest\.com/"))
async def handle_pinterest_link(message: Message):
    url = message.text.strip()
    processing_msg = await message.answer("Анализирую Pinterest ссылку...")

    try:
        if "/pin/" not in url:
            await processing_msg.edit_text("Это не ссылка на Pinterest pin!")
            return

        await processing_msg.edit_text("Скачиваю видео c Pinterest...")
        await send_pinterest_video(message, url)
        await processing_msg.delete()

    except Exception as e:
        await processing_msg.edit_text(f"Ошибка: {e}")
