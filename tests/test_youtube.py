
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import handlers.youtube as youtube


@pytest.mark.asyncio
async def test_download_youtube_mp3(tmp_path):
    url = "https://www.youtube.com/watch?v=abc123"
    format_code = "mp3"

    fake_info = {"id": "abc123", "ext": "mp3"}

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = fake_info
        mock_instance.prepare_filename.return_value = str(
            tmp_path / "abc123.mp3"
        )
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        result = youtube.download_youtube(url, str(tmp_path), format_code)

    assert result.endswith(".mp3")


@pytest.mark.asyncio
async def test_download_youtube_360p(tmp_path):
    url = "https://www.youtube.com/watch?v=abc123"
    format_code = "360p"

    fake_info = {"id": "abc123", "ext": "mp4"}

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = fake_info
        mock_instance.prepare_filename.return_value = str(
            tmp_path / "abc123.mp4"
        )
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        result = youtube.download_youtube(url, str(tmp_path), format_code)

    assert result.endswith(".mp4")


@pytest.mark.asyncio
async def test_download_youtube_720p(tmp_path):
    url = "https://www.youtube.com/watch?v=abc123"
    format_code = "720p"

    fake_info = {"id": "abc123", "ext": "mp4"}

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = fake_info
        mock_instance.prepare_filename.return_value = str(
            tmp_path / "abc123.mp4"
        )
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        result = youtube.download_youtube(url, str(tmp_path), format_code)

    assert result.endswith(".mp4")


@pytest.mark.asyncio
async def test_youtube_keyboard_handler():
    fake_message = AsyncMock()
    fake_message.text = "https://www.youtube.com/watch?v=abc123"

    await youtube.youtube_handler(fake_message)

    fake_message.answer.assert_called_once()
    args, kwargs = fake_message.answer.call_args
    assert "Выбери формат для скачивания:" in args[0]

    kb = kwargs["reply_markup"]
    assert any(btn.text == "360p" for row in kb.inline_keyboard for btn in row)
    assert any(btn.text == "720p" for row in kb.inline_keyboard for btn in row)
    assert any(btn.text == "MP3" for row in kb.inline_keyboard for btn in row)


@pytest.mark.asyncio
async def test_youtube_callback_triggers_download(tmp_path):
    fake_callback = AsyncMock()
    fake_callback.data = "yt:1234abcd:mp3"
    fake_callback.message = AsyncMock()

    youtube.cache["1234abcd"] = {"url": "https://youtu.be/fake"}

    with patch(
        "handlers.youtube.download_youtube",
        return_value=str(tmp_path / "file.mp3"),
    ):
        with open(tmp_path / "file.mp3", "wb") as f:
            f.write(b"testdata")

        await youtube.youtube_callback(fake_callback)

    fake_callback.message.answer_audio.assert_called_once()
