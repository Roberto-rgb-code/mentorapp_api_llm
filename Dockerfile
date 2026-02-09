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

# Copiar el resto del código
COPY . .

# Puerto (Railway inyecta PORT; local usa 8000)
ENV PORT=8000
EXPOSE 8000

# Comando: usa $PORT en Railway, 8000 local
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
