FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY requirements.txt .


RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --upgrade yt-dlp



COPY . .

CMD ["python", "main.py"]