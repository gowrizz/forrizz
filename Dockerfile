FROM python:3.10-slim

WORKDIR /app
COPY app/ /app

RUN apt-get update && apt-get install -y libsndfile1 ffmpeg && \
    pip install --no-cache-dir runpod && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "handler.py"]