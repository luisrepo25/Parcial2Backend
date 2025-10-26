# Imagen base
FROM python:3.12-slim

# Evita bytecode y buffers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Crea usuario no root
RUN useradd -m appuser

# Dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Instala deps primero (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el proyecto
COPY app ./app
#opcional en dev; en prod, inyectar vía secrets/env del orquestador
COPY .env ./.env 
# Permisos
RUN chown -R appuser:appuser /app
USER appuser

# Exponer puerto
EXPOSE 8000

# Comando por defecto: gunicorn (producción ligera)
CMD ["gunicorn", "project.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "3"]
