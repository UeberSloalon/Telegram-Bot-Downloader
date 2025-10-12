import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

from handlers.pinterest import router, extract_video_url, send_pinterest_video


class TestPinterestBot:

    @pytest.fixture
    def mock_message(self):
        message = Mock()
        message.text = "https://www.pinterest.com/pin/123456/"
        message.answer = AsyncMock()
        message.answer_video = AsyncMock()
        return message

    @pytest.fixture
    def mock_inline_query(self):
        query = Mock()
        query.query = "https://www.pinterest.com/pin/123456/"
        query.answer = AsyncMock()
        return query

    def get_handler_by_callback_name(self, callback_name):
        all_handlers = router.message.handlers + router.inline_query.handlers

        for handler in all_handlers:
            if (
                hasattr(handler, "callback")
                and hasattr(handler.callback, "__name__")
                and handler.callback.__name__ == callback_name
            ):
                return handler.callback
        return None

    @pytest.mark.asyncio
    async def test_extract_video_url_success(self):
        test_url = "https://www.pinterest.com/pin/123456/"
        expected_video_url = "https://example.com/video.mp4"

        with patch("handlers.pinterest.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = Mock()
            mock_instance.extract_info.return_value = {"url": expected_video_url}
            mock_ydl.return_value = mock_instance

            result = await extract_video_url(test_url)

            assert result == expected_video_url
            mock_instance.extract_info.assert_called_once_with(test_url, download=False)

    @pytest.mark.asyncio
    async def test_extract_video_url_with_entries(self):
        test_url = "https://www.pinterest.com/pin/123456/"
        expected_video_url = "https://example.com/video.mp4"

        with patch("handlers.pinterest.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = Mock()
            mock_instance.extract_info.return_value = {
                "entries": [{"url": expected_video_url}]
            }
            mock_ydl.return_value = mock_instance

            result = await extract_video_url(test_url)

            assert result == expected_video_url

    @pytest.mark.asyncio
    async def test_extract_video_url_fallback_to_requests(self):
        test_url = "https://www.pinterest.com/pin/123456/"
        expected_video_url = "https://example.com/video.mp4"
        html_content = f'<video src="{expected_video_url}">'

        with patch("handlers.pinterest.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = Mock()
            mock_instance.extract_info.side_effect = Exception("yt-dlp error")
            mock_ydl.return_value = mock_instance

            with patch("handlers.pinterest.requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = html_content
                mock_get.return_value = mock_response

                result = await extract_video_url(test_url)

                assert result == expected_video_url
                mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_video_url_not_found(self):
        test_url = "https://www.pinterest.com/pin/123456/"

        with patch("handlers.pinterest.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = Mock()
            mock_instance.extract_info.side_effect = Exception("yt-dlp error")
            mock_ydl.return_value = mock_instance

            with patch("handlers.pinterest.requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = "<html>No video here</html>"
                mock_get.return_value = mock_response

                with pytest.raises(Exception, match="Видео URL не найден"):
                    await extract_video_url(test_url)

    @pytest.mark.asyncio
    async def test_send_pinterest_video_success_direct(self, mock_message):
        test_url = "https://www.pinterest.com/pin/123456/"
        video_url = "https://example.com/video.mp4"

        with patch("handlers.pinterest.extract_video_url", return_value=video_url):
            await send_pinterest_video(mock_message, test_url)

            mock_message.answer_video.assert_called_once()
            call_args = mock_message.answer_video.call_args
            assert call_args.kwargs["video"] == video_url
            assert "Cкачано в @SaveTTasrobot" in call_args.kwargs["caption"]

    @pytest.mark.asyncio
    async def test_send_pinterest_video_download_fallback(self, mock_message):
        test_url = "https://www.pinterest.com/pin/123456/"
        video_url = "https://example.com/video.mp4"

        with patch("handlers.pinterest.extract_video_url", return_value=video_url):
            mock_message.answer_video.side_effect = [
                Exception("Direct upload failed"),
                AsyncMock(),
            ]

            with patch("handlers.pinterest.requests.get") as mock_requests_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.iter_content.return_value = [b"fake_video_data"]
                mock_requests_get.return_value = mock_response

                import tempfile
                import os

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".mp4"
                ) as temp_file:
                    temp_file.write(b"fake_video_data")
                    temp_path = temp_file.name

                try:
                    with patch("handlers.pinterest.Path") as mock_path:
                        mock_path.return_value.mkdir.return_value = None
                        mock_path.return_value.__truediv__.return_value = Path(
                            temp_path
                        )

                        with patch("handlers.pinterest.FSInputFile") as mock_fs_input:
                            mock_fs_input.return_value = temp_path

                            await send_pinterest_video(mock_message, test_url)

                            mock_fs_input.assert_called_once()

                finally:
                    # Очистка
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_send_pinterest_video_error_handling(self, mock_message):
        test_url = "https://www.pinterest.com/pin/123456/"

        with patch(
            "handlers.pinterest.extract_video_url",
            side_effect=Exception("Видео URL не найден"),
        ):
            await send_pinterest_video(mock_message, test_url)

            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            assert "Не удалось найти видео" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_pinterest_inline_query_handler_success(self, mock_inline_query):
        video_url = "https://example.com/video.mp4"

        inline_handler = self.get_handler_by_callback_name("pinterest_inline")
        assert inline_handler is not None, "Inline query handler not found"

        with patch("handlers.pinterest.extract_video_url", return_value=video_url):
            await inline_handler(mock_inline_query)

            mock_inline_query.answer.assert_called_once()
            call_args = mock_inline_query.answer.call_args
            results = call_args[0][0]
            assert len(results) == 1
            assert results[0].video_url == video_url
            assert results[0].title == "🎬 Видео с Pinterest"

    @pytest.mark.asyncio
    async def test_pinterest_inline_query_handler_error(self, mock_inline_query):
        inline_handler = self.get_handler_by_callback_name("pinterest_inline")
        assert inline_handler is not None, "Inline query handler not found"

        with patch(
            "handlers.pinterest.extract_video_url",
            side_effect=Exception("Video not found"),
        ):
            await inline_handler(mock_inline_query)

            mock_inline_query.answer.assert_called_once()
            call_args = mock_inline_query.answer.call_args
            results = call_args[0][0]
            assert "Ошибка" in results[0].title

    @pytest.mark.asyncio
    async def test_pinterest_inline_query_no_pinterest_link(self, mock_inline_query):
        mock_inline_query.query = "https://example.com/other-video"

        inline_handler = self.get_handler_by_callback_name("pinterest_inline")
        assert inline_handler is not None, "Inline query handler not found"

        await inline_handler(mock_inline_query)

        mock_inline_query.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_pinit_link_handler_success(self):
        message = Mock()
        message.text = "https://pin.it/abc123"
        message.answer = AsyncMock()

        pin_it_handler = self.get_handler_by_callback_name("handle_pinit_link")
        assert pin_it_handler is not None, "Pin.it handler not found"

        with patch("handlers.pinterest.requests.head") as mock_head:
            mock_response = Mock()
            mock_response.url = "https://www.pinterest.com/pin/123456/"
            mock_head.return_value = mock_response

            with patch(
                "handlers.pinterest.send_pinterest_video", AsyncMock()
            ) as mock_send:
                await pin_it_handler(message)

                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_pinterest_link_handler_success(self):
        message = Mock()
        message.text = "https://www.pinterest.com/pin/123456/"
        message.answer = AsyncMock()

        pinterest_handler = self.get_handler_by_callback_name("handle_pinterest_link")
        assert pinterest_handler is not None, "Pinterest handler not found"

        with patch("handlers.pinterest.send_pinterest_video", AsyncMock()) as mock_send:
            await pinterest_handler(message)

            mock_send.assert_called_once()

    @pytest.mark.asyncio
    def test_router_handlers_registered(self):
        assert len(router.message.handlers) >= 2, "Not enough message handlers"
        assert len(router.inline_query.handlers) >= 1, "No inline query handlers"

        handler_names = []
        for handler in router.message.handlers + router.inline_query.handlers:
            if hasattr(handler, "callback") and hasattr(handler.callback, "__name__"):
                handler_names.append(handler.callback.__name__)

        expected_handlers = [
            "handle_pinit_link",
            "handle_pinterest_link",
            "pinterest_inline",
        ]
        for expected in expected_handlers:
            assert expected in handler_names, f"Handler {expected} not found"

    def test_direct_function_calls(self):

        assert callable(extract_video_url)
        assert callable(send_pinterest_video)
        assert router is not None

    @pytest.mark.asyncio
    async def test_integration_style_test(self):
        message = Mock()
        message.text = "https://www.pinterest.com/pin/123456/"
        message.answer = AsyncMock()
        message.answer_video = AsyncMock()

        with patch("handlers.pinterest.extract_video_url") as mock_extract:
            mock_extract.return_value = "https://example.com/video.mp4"

            await send_pinterest_video(message, "https://www.pinterest.com/pin/123456/")

            message.answer_video.assert_called_once()
