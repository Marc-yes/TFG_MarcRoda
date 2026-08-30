FROM python:3.12-slim

# Evita que Python guardi fitxers pyc i assegura sortides de log en calent
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instal·lem llibreries necessàries per a FAISS (libgomp1) i compilacions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiem i instal·lem dependències de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem el codi font
COPY . .

EXPOSE 5001

CMD ["python", "api.py"]
