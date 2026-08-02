FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY ai_model/ ./ai_model/
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.app:app"]