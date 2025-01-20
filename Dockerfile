FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    git \
    git-lfs \
    curl \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

COPY app/ /app

RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \
    pip3 install --no-cache-dir runpod && \
    pip3 install --no-cache-dir -r requirements.txt && \
    python3 -c "from resemble_enhance.enhancer.download import download; download()"

CMD ["python", "-u", "handler.py"]
