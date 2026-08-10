# Usar una imagen oficial de Python como base
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc en el disco y habilitar el volcado de salida directo a la terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python con control de memoria
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del proyecto al contenedor
COPY . .

# Asegurar la existencia de las carpetas para la base de datos y reportes
RUN mkdir -p datos reportes

# Comando por defecto para ejecutar el menú interactivo
CMD ["python", "main.py"]
