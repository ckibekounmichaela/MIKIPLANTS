FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet dans /app
COPY . .

# Se placer dans backend/ : main.py trouve routers/, services/, database.py, etc.
WORKDIR /app/backend

# Créer le dossier uploads (UPLOADS_DIR = /app/uploads)
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
