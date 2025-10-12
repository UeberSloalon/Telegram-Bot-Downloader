from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import handlers.tiktok as tiktok


@pytest.mark.asyncio
async def test_download_tiktok():

    mock_message = AsyncMock()
    mock_message.text = "https://www.tiktok.com/@test/video/123"
    mock_message.answer = AsyncMock()
    mock_message.answer_video = AsyncMock()

    with patch("handlers.tiktok.yt_dlp.YoutubeDL") as mock_ytdlp, patch(
        "handlers.tiktok.FSInputFile"
    ) as mock_fs_input, patch("handlers.tiktok.os.makedirs"), patch(
        "handlers.tiktok.os.remove"
    ):

        mock_instance = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        mock_fs_input.return_value = "mock_video_file"

        await tiktok.download_tiktok(mock_message)

        mock_message.answer.assert_any_call("Скачиваю видео с TikTok...")
        mock_message.answer_video.assert_called_once()
