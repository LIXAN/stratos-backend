FROM python:3.11-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA (Importante para PostgreSQL)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Exponer el puerto (Asegúrate que en DigitalOcean pusiste el 8000)
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]