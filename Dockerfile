# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install django==4.2.7 djangorestframework==3.14.0 django-cors-headers==4.3.1 \
    django-redis==5.4.0 celery==5.3.4 redis==5.0.1 psycopg2-binary==2.9.7 \
    gunicorn==21.2.0 uvicorn==0.24.0 python-telegram-bot==20.7 \
    python-decouple==3.8 django-environ==0.11.2 whitenoise==6.6.0 \
    flower==2.0.1 django-extensions==3.2.3 pillow==10.1.0 \
    django-filter==23.5

# Copy project
COPY . .

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "noti.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gunicorn.workers.sync.SyncWorker"]
