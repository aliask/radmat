FROM python:3.13-slim@sha256:6f79e7a10bb7d0b0a50534a70ebc78823f941fba26143ecd7e6c5dca9d7d7e8a

LABEL org.opencontainers.image.authors="aliask"
LABEL org.opencontainers.image.source="https://github.com/aliask/radmat"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.title="RADMAT"
LABEL org.opencontainers.image.description="Really Awesome Display of Meteorologic / Atmospheric Things (RADMAT)"

WORKDIR /app

# Upgrade pip and install wheel
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt /app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/* .
CMD [ "python3", "main.py" ]
