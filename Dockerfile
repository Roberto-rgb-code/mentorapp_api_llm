# Usar imagen oficial de Python como base
FROM python:3.10-slim

# Variables de entorno (no muestra los logs en buffer)
ENV PYTHONUNBUFFERED=1

# Crear y establecer directorio de trabajo
WORKDIR /code

# Copiar archivos de dependencias primero
COPY requirements.txt ./

# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto del código (incluye start.sh)
COPY . .
RUN chmod +x start.sh

# Puerto (Railway inyecta PORT; local usa 8000)
ENV PORT=8000
EXPOSE 8000

# Script lee PORT del entorno (evita error "$PORT is not a valid integer")
CMD ["./start.sh"]
