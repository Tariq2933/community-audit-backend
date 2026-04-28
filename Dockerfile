FROM python:3.11-slim

WORKDIR /app

# System deps required by Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libasound2 \
    libxshmfence1 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxfixes3 \
    libxcb1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Playwright browsers
RUN playwright install chromium

COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
