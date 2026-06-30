# Dockerfile
FROM python:3.11-slim

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy both the library module and the app folder
COPY rate_limiter/ /workspace/rate_limiter/
COPY app/ /workspace/app/

# Run the Uvicorn server pointing to our app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]