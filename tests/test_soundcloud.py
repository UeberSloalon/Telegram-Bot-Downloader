import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil

from handlers.soundcloud import (
    get_url_hash,
    store_url,
    get_url,
    download_sc_track_simple,
    download_sc_album,
    url_storage,
    handle_sc,
    handle_album_callback,
    handle_track_callback,
)


class TestSoundCloudFunctions:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_url = "https://soundcloud.com/user/test-track"
        self.test_album_url = "https://soundcloud.com/user/sets/test-album"
        url_storage.clear()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_url_hashing(self):
        hash1 = get_url_hash(self.test_url)
        hash2 = get_url_hash(self.test_url)

        assert hash1 == hash2
        assert len(hash1) == 10

    def test_url_storage(self):
        hash_key = store_url(self.test_url)

        assert hash_key in url_storage
        assert url_storage[hash_key] == self.test_url
        assert get_url(hash_key) == self.test_url

    @pytest.mark.asyncio
    async def test_download_sc_track_simple_success(self):
        with patch("handlers.soundcloud.run_yt_dlp_with_timeout"):
            with patch("handlers.soundcloud.Path.exists", return_value=True):
                result = await download_sc_track_simple(self.test_url)
                assert isinstance(result, Path)

    @pytest.mark.asyncio
    async def test_download_sc_track_simple_file_not_found(self):
        with patch("handlers.soundcloud.run_yt_dlp_with_timeout"):
            with patch("handlers.soundcloud.Path.exists", return_value=False):
                with pytest.raises(FileNotFoundError):
                    await download_sc_track_simple(self.test_url)

    @pytest.mark.asyncio
    async def test_download_sc_album_success(self):
        with patch("handlers.soundcloud.run_yt_dlp_with_timeout"):
            with patch("handlers.soundcloud.Path.glob") as mock_glob:
                mock_files = [Mock(spec=Path, is_file=lambda: True) for _ in range(2)]
                mock_glob.return_value = mock_files

                with patch("handlers.soundcloud.zipfile.ZipFile"):
                    result = await download_sc_album(self.test_album_url)
                    assert isinstance(result, Path)

    @pytest.mark.asyncio
    async def test_download_sc_album_no_files(self):
        with patch("handlers.soundcloud.run_yt_dlp_with_timeout"):
            with patch("handlers.soundcloud.Path.glob", return_value=[]):
                with pytest.raises(Exception, match="Не удалось скачать файлы альбома"):
                    await download_sc_album(self.test_album_url)


class TestRouterHandlers:

    def setup_method(self):
        self.message = AsyncMock()
        self.callback_query = AsyncMock()

        self.message.text = "https://soundcloud.com/user/sets/test-album"
        self.callback_query.data = "a_abc123"
        self.callback_query.message = AsyncMock()

    @pytest.mark.asyncio
    async def test_handle_sc_album_url(self):
        with patch("handlers.soundcloud.store_url", return_value="test_hash"):
            with patch("handlers.soundcloud.InlineKeyboardMarkup"):
                with patch("handlers.soundcloud.InlineKeyboardButton"):
                    await handle_sc(self.message)
                    self.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_sc_track_url(self):
        self.message.text = "https://soundcloud.com/user/track"

        with patch("handlers.soundcloud.download_sc_track_simple") as mock_download:
            with patch("handlers.soundcloud.FSInputFile"):
                mock_path = Mock()
                mock_path.unlink = Mock()
                mock_download.return_value = mock_path

                mock_status = AsyncMock()
                self.message.answer.return_value = mock_status

                await handle_sc(self.message)

                mock_download.assert_called_once()
                mock_status.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_album_callback_valid_hash(self):
        with patch("handlers.soundcloud.get_url", return_value=self.message.text):
            with patch("handlers.soundcloud.download_sc_album") as mock_download:
                with patch("handlers.soundcloud.FSInputFile"):
                    mock_file = Mock()
                    mock_file.stat.return_value.st_size = 1000
                    mock_file.unlink = Mock()
                    mock_download.return_value = mock_file

                    await handle_album_callback(self.callback_query)

                    mock_download.assert_called_once()
                    self.callback_query.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_album_callback_invalid_hash(self):
        with patch("handlers.soundcloud.get_url", return_value=""):
            await handle_album_callback(self.callback_query)

            actual_call = self.callback_query.message.edit_text.call_args[0][0]
            assert "Ссылка устарела. Отправьте ссылку заново." in actual_call

    @pytest.mark.asyncio
    async def test_handle_track_callback(self):
        with patch("handlers.soundcloud.get_url", return_value=self.message.text):
            with patch("handlers.soundcloud.download_sc_track_simple") as mock_download:
                with patch("handlers.soundcloud.FSInputFile"):
                    mock_path = Mock()
                    mock_path.unlink = Mock()
                    mock_download.return_value = mock_path

                    await handle_track_callback(self.callback_query)

                    mock_download.assert_called_once()
                    self.callback_query.message.edit_text.assert_called_once()


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://soundcloud.com/user/sets/album", True),
        ("https://soundcloud.com/user/playlists/123", True),
        ("https://soundcloud.com/user/albums/test", True),
        ("https://soundcloud.com/user/track", False),
    ],
)
def test_album_detection(url, expected):
    is_album = any(
        keyword in url.lower() for keyword in ["/sets/", "/playlists/", "/albums/"]
    )
    assert is_album == expected
