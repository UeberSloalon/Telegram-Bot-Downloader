from unittest.mock import MagicMock, patch

import pytest

from handlers import instagram


@pytest.mark.asyncio
async def test_download_instagram_single_video(tmp_path):
    url = "https://www.instagram.com/reel/abc123/"

    fake_info = {"id": "abc123", "ext": "mp4"}

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = fake_info
        mock_instance.prepare_filename.return_value = str(
            tmp_path / "abc123.mp4"
        )
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        result = instagram.download_instagram(url, str(tmp_path))

    assert len(result) == 1
    assert result[0].endswith(".mp4")


@pytest.mark.asyncio
async def test_download_instagram_playlist(tmp_path):
    url = "https://www.instagram.com/reel/playlist123/"

    fake_info = {
        "entries": [
            {"id": "vid1", "ext": "mp4"},
            {"id": "vid2", "ext": "mp4"},
        ]
    }

    with patch("yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = fake_info
        mock_instance.prepare_filename.side_effect = [
            str(tmp_path / "vid1.mp4"),
            str(tmp_path / "vid2.mp4"),
        ]
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        result = instagram.download_instagram(url, str(tmp_path))

    assert len(result) == 2
    assert all(path.endswith(".mp4") for path in result)
