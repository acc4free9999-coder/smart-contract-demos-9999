FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ARM64-compatible Solidity compiler
RUN npm install -g solc@0.8.19

RUN solcjs --version

COPY blockchain-deploy/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY contracts ./contracts
COPY blockchain-deploy/deploy.py .

RUN mkdir -p /shared

CMD ["python", "deploy.py"]