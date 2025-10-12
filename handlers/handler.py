from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import BotCommand, Message

router = Router()


@router.message(CommandStart())
async def start_bot(message: Message):
    await message.answer(
        "👋 Привет!\n\n"
        "📥 Я скачиваю фото/видео с YouTube, TikTok, Instagram, Pinterest, Soundcloud без водяных знаков.\n\n"
        "🚀 Отправь ссылку на фото/видео – и я загружу его!"
    )


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота 🚀"),
    ]
    await bot.set_my_commands(commands)



