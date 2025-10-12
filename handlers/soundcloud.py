import asyncio
import uuid
import zipfile
import hashlib
from pathlib import Path

import yt_dlp
from aiogram import F, Router
from aiogram.types import FSInputFile, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

router = Router()

DOWNLOAD_DIR = Path("downloads/soundcloud_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

url_storage = {}


def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:10]


def store_url(url: str) -> str:
    url_hash = get_url_hash(url)
    url_storage[url_hash] = url
    return url_hash


def get_url(hash: str) -> str:
    return url_storage.get(hash, "")


async def download_sc_track(url: str) -> Path:
    filepath = DOWNLOAD_DIR / f"soundcloud_{uuid.uuid4().hex}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(filepath) + '.%(ext)s',
        'quiet': False,
        'noplaylist': True,
        'extractaudio': True,
        'audioformat': 'mp3',
        'http_chunk_size': 10485760,
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'extract_flat': False,
        'socket_timeout': 30,
        'extractor_retries': 3,
        'noprogress': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        await run_yt_dlp_with_timeout(url, ydl_opts, timeout=300)

        for ext in ['mp3', 'm4a', 'webm']:
            potential_file = filepath.with_suffix(f'.{ext}')
            if potential_file.exists():
                return potential_file

        audio_files = list(DOWNLOAD_DIR.glob(f"{filepath.stem}.*"))
        if audio_files:
            return audio_files[0]

        raise FileNotFoundError("Скачанный файл не найден")

    except Exception as e:
        for partial_file in DOWNLOAD_DIR.glob(f"{filepath.stem}.*"):
            try:
                partial_file.unlink()
            except:
                pass
        raise e


async def download_sc_album(url: str) -> Path:
    album_dir = DOWNLOAD_DIR / f"album_{uuid.uuid4().hex}"
    album_dir.mkdir()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(album_dir / '%(title)s.%(ext)s'),
        'quiet': False,
        'noplaylist': False,
        'extractaudio': True,
        'audioformat': 'mp3',
        'http_chunk_size': 10485760,
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'socket_timeout': 30,
        'extractor_retries': 3,
        'noprogress': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    downloaded_files = []

    try:
        await run_yt_dlp_with_timeout(url, ydl_opts, timeout=1800)

        audio_files = list(album_dir.glob("*.mp3"))
        if not audio_files:
            raise Exception("Не удалось скачать файлы альбома")

        downloaded_files = audio_files

        zip_path = DOWNLOAD_DIR / f"{album_dir.name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in audio_files:
                zipf.write(file_path, file_path.name)

        return zip_path

    except asyncio.TimeoutError:
        if downloaded_files:
            zip_path = DOWNLOAD_DIR / f"{album_dir.name}_partial.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in downloaded_files:
                    zipf.write(file_path, file_path.name)
            return zip_path
        else:
            raise Exception("Таймаут при скачивании альбома")
    finally:
        for file_path in album_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        try:
            album_dir.rmdir()
        except:
            pass


async def run_yt_dlp_with_timeout(url: str, options: dict, timeout: int = 300):

    def _task():
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as e:
            if "Unable to download webpage" in str(e) or "fragment" in str(e).lower():
                print(f"Первая попытка не удалась: {e}. Пробуем альтернативный метод...")
                options_copy = options.copy()
                options_copy.pop('postprocessors', None)
                options_copy.pop('extractaudio', None)
                options_copy['format'] = 'best'
                with yt_dlp.YoutubeDL(options_copy) as ydl_alt:
                    ydl_alt.download([url])
            else:
                raise e

    await asyncio.wait_for(
        asyncio.get_event_loop().run_in_executor(None, _task),
        timeout=timeout
    )


async def download_sc_track_simple(url: str) -> Path:
    filepath = DOWNLOAD_DIR / f"soundcloud_{uuid.uuid4().hex}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(filepath)[:-4] + '.%(ext)s',
        'quiet': False,
        'noplaylist': True,
        'extractaudio': False,
        'audioformat': 'mp3',
        'retries': 2,
        'fragment_retries': 2,
        'skip_unavailable_fragments': True,
        'socket_timeout': 20,
        'extractor_retries': 2,
    }

    try:
        await run_yt_dlp_with_timeout(url, ydl_opts, timeout=180)

        for ext in ['mp3', 'm4a', 'webm']:
            potential_file = filepath.with_suffix(f'.{ext}')
            if potential_file.exists():
                if ext != 'mp3':
                    mp3_file = filepath.with_suffix('.mp3')
                    await convert_to_mp3(potential_file, mp3_file)
                    potential_file.unlink()
                    return mp3_file
                return potential_file

        raise FileNotFoundError("Скачанный файл не найден")

    except Exception as e:
        for partial_file in DOWNLOAD_DIR.glob(f"{filepath.stem}.*"):
            try:
                partial_file.unlink()
            except:
                pass
        raise e


async def convert_to_mp3(input_file: Path, output_file: Path):

    def _convert():
        import subprocess
        subprocess.run([
            'ffmpeg', '-i', str(input_file),
            '-codec:a', 'libmp3lame', '-qscale:a', '2',
            str(output_file), '-y'
        ], check=True, capture_output=True)

    await asyncio.get_event_loop().run_in_executor(None, _convert)


@router.message(Command("album"))
async def handle_sc_album_command(message: Message):
    if not message.text or len(message.text.split()) < 2:
        await message.answer("Использование: /album <ссылка на альбом SoundCloud>")
        return

    url = message.text.split()[1].strip()
    status = await message.answer(" Скачиваю альбом с SoundCloud... Это может занять несколько минут.")

    try:
        file_path = await download_sc_album(url)
        file_size = file_path.stat().st_size

        if file_size == 0:
            await message.answer("Не удалось скачать альбом (пустой файл)")
            file_path.unlink()
            return

        await message.answer_document(
            document=FSInputFile(file_path),
            caption=" Альбом скачан! @SaveTTasrobot"
        )
        file_path.unlink()
    except asyncio.TimeoutError:
        await message.answer(" Таймаут при скачивании альбома. Попробуйте позже или скачайте треки по отдельности.")
    except Exception as e:
        await message.answer(f"Ошибка при скачивании альбома: {str(e)}")
    finally:
        await status.delete()


@router.message(F.text.regexp(r"https?://(www\.)?soundcloud\.com/"))
async def handle_sc(message: Message):

    url = message.text.strip()


    is_album = any(keyword in url.lower() for keyword in ['/sets/', '/playlists/', '/albums/'])

    if is_album:

        url_hash = store_url(url)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📦 Весь альбом", callback_data=f"a_{url_hash}"),
                    InlineKeyboardButton(text="🎵 Первый трек", callback_data=f"t_{url_hash}")
                ]
            ]
        )

        await message.answer(
            " Обнаружен альбом/плейлист. Что скачать?",
            reply_markup=keyboard
        )
    else:
        status = await message.answer(" Скачиваю трек с SoundCloud...")
        try:
            file_path = await download_sc_track_simple(url)
            await message.answer_audio(
                audio=FSInputFile(file_path),
                caption=" Скачано! @SaveTTasrobot"
            )
            file_path.unlink()
        except asyncio.TimeoutError:
            await message.answer(" Таймаут при скачивании трека. Попробуйте еще раз.")
        except Exception as e:
            await message.answer(f" Ошибка при скачивании: {str(e)}")
        finally:
            await status.delete()


@router.callback_query(F.data.startswith("a_"))
async def handle_album_callback(callback_query: CallbackQuery):
    url_hash = callback_query.data[2:]
    url = get_url(url_hash)

    if not url:
        await callback_query.message.edit_text(" Ссылка устарела. Отправьте ссылку заново.")
        return

    await callback_query.message.edit_text(" Скачиваю альбом... Это может занять время...")

    try:
        file_path = await download_sc_album(url)
        file_size = file_path.stat().st_size

        if file_size == 0:
            await callback_query.message.answer(" Не удалось скачать альбом (пустой файл)")
            file_path.unlink()
            return

        await callback_query.message.answer_document(
            document=FSInputFile(file_path),
            caption="Альбом скачан! @SaveTTasrobot"
        )
        file_path.unlink()
    except asyncio.TimeoutError:
        await callback_query.message.answer(" Таймаут при скачивании альбома. Попробуйте позже.")
    except Exception as e:
        await callback_query.message.answer(f"Ошибка при скачивании альбома: {str(e)}")


@router.callback_query(F.data.startswith("t_"))
async def handle_track_callback(callback_query: CallbackQuery):
    url_hash = callback_query.data[2:]
    url = get_url(url_hash)

    if not url:
        await callback_query.message.edit_text("Ссылка устарела. Отправьте ссылку заново.")
        return

    await callback_query.message.edit_text(" Скачиваю трек...")

    try:
        file_path = await download_sc_track_simple(url)
        await callback_query.message.answer_audio(
            audio=FSInputFile(file_path),
            caption=" Скачано! @SaveTTasrobot"
        )
        file_path.unlink()
    except asyncio.TimeoutError:
        await callback_query.message.answer("Таймаут при скачивании трека. Попробуйте еще раз.")
    except Exception as e:
        await callback_query.message.answer(f" Ошибка при скачивании: {str(e)}")