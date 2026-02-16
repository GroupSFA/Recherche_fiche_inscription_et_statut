FROM python:3.11-slim

# Empêche les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Installer les dépendances système nécessaires à Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Installer Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Installer ChromeDriver compatible avec la version de Chrome installée
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    CHROME_MAJOR=$(echo $CHROME_VERSION | cut -d '.' -f 1) && \
    CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_MAJOR") && \
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf chromedriver-linux64.zip chromedriver-linux64

WORKDIR /app

# Copier d'abord requirements pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

EXPOSE 10000

CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0", "--server.headless=true"]
