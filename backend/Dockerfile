# DivisionUp API — imagen del backend (FastAPI)
FROM python:3.12-slim

WORKDIR /app

# Dependencias primero (mejor cacheo de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación + migraciones + tests (pytest corre en la VM)
COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY tests ./tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
