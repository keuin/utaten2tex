FROM debian:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip \
    texlive-xetex \
    texlive-lang-japanese texlive-lang-chinese \
    fonts-noto-cjk fonts-noto-cjk-extra && \
    apt-get autoclean && \
    apt-get --purge --yes autoremove && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

ENTRYPOINT ["python3", "web.py"]