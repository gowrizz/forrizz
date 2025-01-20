FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    python3.10 \
    python3.10-distutils \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    git \
    git-lfs \
    curl \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

RUN pip3 install --no-cache-dir torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

COPY app/requirements.txt /app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ /app/

RUN python3 -c "from resemble_enhance.enhancer.download import download; download()"

CMD ["python3", "-u", "handler.py"]
