FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /root/.cache/piper

CMD ["sh", "-c", "ollama serve & sleep 5 && ollama pull ${OLLAMA_MODEL:-llama3.2} && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
