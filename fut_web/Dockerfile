# Imagen opcional para Render "Docker" service.
# Incluye LibreOffice para poder generar también el PDF (no solo el .docx).
# Si no necesitas PDF, usa el deploy nativo Python (render.yaml) que es
# más liviano y rápido de compilar.

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000
EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 180
