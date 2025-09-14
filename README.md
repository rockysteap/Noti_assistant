# Noti - Django + Telegram Bot Notification System

A modern notification system built with Django REST Framework backend and Telegram bot frontend.

## 🏗️ Architecture

- **Backend**: Django + Django REST Framework
- **Frontend**: Telegram Bot
- **Database**: PostgreSQL
- **Cache/Sessions**: Redis
- **Web Server**: Nginx
- **Application Server**: Gunicorn with Uvicorn workers
- **Task Queue**: Celery
- **Containerization**: Docker + Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/rockysteap/Noti_assistant.git
   cd Noti_assistant
   ```

2. **Environment Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Run initial setup**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Flower (Celery monitoring): http://localhost:5555

## 📁 Project Structure

```
Noti/
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Django application container
├── nginx/                      # Nginx configuration
│   ├── nginx.conf
│   └── conf.d/
│       └── default.conf
├── changes.md                  # Project change tracking
├── env.example                 # Environment variables template
├── init.sql                    # Database initialization
└── README.md                   # This file
```

## 🔧 Services

### Web (Django)
- **Port**: 8000
- **Container**: `noti_web`
- **Description**: Main Django application with Gunicorn + Uvicorn workers

### Database (PostgreSQL)
- **Port**: 5432
- **Container**: `noti_db`
- **Description**: PostgreSQL database with health checks

### Redis
- **Port**: 6379
- **Container**: `noti_redis`
- **Description**: Redis for caching, sessions, and task queues

### Nginx
- **Port**: 80, 443
- **Container**: `noti_nginx`
- **Description**: Reverse proxy with rate limiting and static file serving

### Celery Worker
- **Container**: `noti_celery`
- **Description**: Background task processing

### Celery Beat
- **Container**: `noti_celery_beat`
- **Description**: Scheduled task management

### Flower
- **Port**: 5555
- **Container**: `noti_flower`
- **Description**: Celery task monitoring interface

## 🛠️ Development

### Running Commands

```bash
# Run Django management commands
docker-compose exec web python manage.py <command>

# View logs
docker-compose logs -f web

# Access Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test
```

### Database Operations

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## 🔐 Environment Variables

Copy `env.example` to `.env` and configure:

- **Database**: PostgreSQL connection settings
- **Redis**: Cache and session storage
- **Telegram**: Bot token and webhook URL
- **Email**: SMTP settings for notifications
- **Security**: CORS and CSRF settings

## 📊 Monitoring

- **Flower**: http://localhost:5555 - Celery task monitoring
- **Nginx Logs**: Available in container logs
- **Database**: PostgreSQL logs via Docker

## 🚀 Production Deployment

1. Update environment variables for production
2. Configure SSL certificates in `nginx/ssl/`
3. Set up proper domain names
4. Configure backup strategies
5. Set up monitoring and logging

## 📝 Change Tracking

All project changes are tracked in `changes.md`. This file contains:
- Development phases and progress
- Implementation details
- Environment variable documentation
- Security notes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Update `changes.md` with your modifications
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
