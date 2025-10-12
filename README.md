# 📥 Telegram Bot Downloader  

Телеграм-бот для скачивания видео и музыки с популярных платформ (**YouTube, Instagram, SoundCloud и др.**) с использованием [`aiogram`](https://docs.aiogram.dev) и [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).  

Бот работает как в обычном режиме (по ссылкам в чате), так и через **inline-режим** — можно сразу искать и качать видео/аудио.  

---

## ✨ Возможности

- 📹 Скачивание видео с **YouTube** (с выбором качества: `360p`, `720p`, `MP3`).
- 🎶 Скачивание треков с **SoundCloud**.
- 📸 Скачивание **Instagram** постов, Reels, IGTV (поддержка альбомов).
- ⚡ Быстрая выдача файлов через inline.
- 🧹 Автоматическая очистка временных файлов после отправки.
- 🐳 Запуск через **Docker** (изолированное окружение, удобное развёртывание).
- 🔑 Конфигурация через `.env` файл.

---

## 🚀 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/username/telegram-bot-downloader.git
cd telegram-bot-downloader
```
### 2. Настройка окружения

Создайте файл .env в корне проекта:
```bash
BOT_TOKEN=your_telegram_bot_token
```
Получить токен можно у [`BotFather`](https://t.me/BotFather).

---
## 🔧 Запуск без Docker (локально)

Установите зависимости:
``` bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

Запустите бота:
```bash
python main.py
```

### 🐳 Запуск через Docker

1.Соберите контейнер:
```
docker build -t telegram-bot-downloader .
```

2.Запустите контейнер:
```
docker run -d --name mybot --env-file .env telegram-bot-downloader
```
---
## 📁 Структура проекта
```bash
telegram-bot-downloader/
├── handlers/              # Хэндлеры для разных сервисов (YouTube, Instagram, SoundCloud)
│   ├── __init__.py
│   ├── handler.py
│   ├── instagram.py
│   ├── pinterest.py
│   ├── soundcloud.py
│   ├── tiktok.py
│   └── youtube.py
├── downloads/            # Временные файлы (очищаются автоматически)
├── main.py               # Точка входа
├── requirements.txt      # Зависимости
├── Dockerfile            # Docker сборка
├── .dockerignore         # Исключения для Docker
└── README.md             # Документация
```
---
## 🛠 Используемые технологии

- [`Python 3.11+`](https://www.python.org/)

- [`aiogram 3.x`](https://docs.aiogram.dev)
 — фреймворк для Telegram-ботов.

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)
 — скачивание видео/аудио.

- [`Docker`](https://www.docker.com/)
 — для развёртывания.

## 📌 Примеры использования
### 1. YouTube

Пользователь отправляет ссылку:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Бот отвечает:
```
Выбери формат для скачивания:
[360p] [720p] [MP3]
```

После выбора — сразу отправляется готовый файл.

### 2. Instagram

Пользователь кидает ссылку на пост:
```
https://www.instagram.com/reel/xxxxxxx
```

Бот скачивает и отправляет видео или фото.
Если в посте несколько медиафайлов (альбом) — бот отправит их все.

### 3. SoundCloud

Пользователь кидает ссылку:
```
https://soundcloud.com/artist/track
```



---
🐛 Возможные ошибки и решения
---
- ERROR: ffprobe and ffmpeg not found
→ Установите ffmpeg внутри контейнера или локально:
```
sudo apt-get update && sudo apt-get install -y ffmpeg
```

- BUTTON_DATA_INVALID
→ Слишком длинный callback_data для кнопок. Нужно ограничить до 64 байт.

---