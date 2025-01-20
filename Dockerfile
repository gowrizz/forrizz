FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    libsndfile1 \
    ffmpeg \
    git \
    git-lfs \
    curl \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

COPY app/ /app

RUN pip install --no-cache-dir runpod && \
    pip install --no-cache-dir -r requirements.txt && \
    python -c "from resemble_enhance.enhancer.download import download; download()"

CMD ["python", "-u", "handler.py"]
