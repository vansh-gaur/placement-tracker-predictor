FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Train first (ml/train.py) so backend/model.pkl exists before building,
# otherwise the API starts but /api/predict returns 503 until a model is added.
ENV PORT=5000
EXPOSE 5000
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:$PORT app:app"]
