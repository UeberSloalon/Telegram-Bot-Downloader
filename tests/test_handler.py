import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message

from handlers.handler import start_bot, set_commands

class TestStartBot:
    @pytest.mark.asyncio
    async def test_start_command(self):
        message = AsyncMock(spec=Message)
        message.answer = AsyncMock()

        await start_bot(message)

        message.answer.assert_called_once()


        actual_text = message.answer.call_args[0][0]
        expected_text = (
            "👋 Привет!\n\n"
            "📥 Я скачиваю фото/видео с YouTube, TikTok, Instagram, Pinterest, Soundcloud без водяных знаков.\n\n"
            "🚀 Отправь ссылку на фото/видео – и я загружу его!"
        )

        assert actual_text == expected_text


    @pytest.mark.asyncio
    async def test_set_commands(self):
        bot = AsyncMock()

        await set_commands(bot)

        bot.set_my_commands.assert_called_once()
        commands = bot.set_my_commands.call_args[0][0]
        assert len(commands) == 1
        assert commands[0].command == "start"
        assert commands[0].description == "Запустить бота 🚀"