FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY pytest.ini .

# Create directory for DB
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run with Gunicorn for production (install it first)
# CMD ["gunicorn", "backend.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Or use uvicorn directly (simpler)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
