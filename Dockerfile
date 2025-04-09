FROM python:3.13-slim@sha256:21e39cf1815802d4c6f89a0d3a166cc67ce58f95b6d1639e68a394c99310d2e5

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
