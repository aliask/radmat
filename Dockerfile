FROM python:3.13-slim@sha256:f7fa672880bbbc16d119ee7bd05e91609092f46137be1d3a85e1fc66dd60bc74

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
