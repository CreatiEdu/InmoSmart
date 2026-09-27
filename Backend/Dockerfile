# Usar imagen base ligera de Python
# Imagen base oficial de Python limpia (versión slim para ahorrar espacio)
FROM python:3.12.14-slim-trixie


# Evita que Python escriba archivos .pyc en el disco y fuerza que la salida de la terminal no use buffer (ideal para ver logs en tiempo real)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema requeridas para algunas librerías de Python (como PostgreSQL, Pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev pkg-config default-libmysqlclient-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia todo el código del proyecto local al contenedor
COPY . /app/
RUN pip install --upgrade pip && pip install -r requirements.txt


# Expone el puerto donde se ejecutará Django
EXPOSE 8000

# Comando para iniciar el servidor de desarrollo de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]