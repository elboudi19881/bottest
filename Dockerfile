# Stage 1: Build
FROM python:3.10-slim AS builder

# Setzen des Arbeitsverzeichnisses
WORKDIR /app

# Kopieren der requirements.txt
COPY requirements.txt .

# Installation der Abhängigkeiten
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

# Stage 2: Runtime
FROM python:3.10-slim

# Setzen des Arbeitsverzeichnisses
WORKDIR /app

# Setzen von Umgebungsvariablen
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Kopieren der installierten Abhängigkeiten aus dem Builder-Stage
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Kopieren des Quellcodes
COPY . .

# Exponieren des Ports für die Flask-App
EXPOSE 5000

# Starten der Flask-App mit Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]