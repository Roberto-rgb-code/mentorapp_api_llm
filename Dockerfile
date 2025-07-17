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

# Exponer el puerto donde corre FastAPI
EXPOSE 8000

# Comando para correr la app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
