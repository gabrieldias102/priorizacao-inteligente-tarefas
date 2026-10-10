# Contexto de build: a pasta ml/, para o serviço levar junto os modelos treinados.
FROM python:3.12-slim
WORKDIR /app
COPY service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY service/app ./app
COPY models ./models
ENV MODELO_CAMINHO=/app/models/modelo-v1.joblib
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
