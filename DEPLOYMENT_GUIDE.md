# Secure Result Platform - Deployment Guide

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment Options](#cloud-deployment-options)
   - [Azure App Service](#azure-app-service)
   - [AWS Elastic Beanstalk](#aws-elastic-beanstalk)
   - [Heroku](#heroku)
4. [Security Configuration](#security-configuration)
5. [Testing the API](#testing-the-api)

---

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 16+ (for React frontend)
- PostgreSQL (optional, can use SQLite for development)

### Backend Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd secure-result-platform

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your configurations

# 5. Initialize database
python -c "from app import init_db; init_db()"

# 6. Run the application
python app.py
# Or with gunicorn:
gunicorn --bind 0.0.0.0:5000 app:app
```

Backend will be available at `http://localhost:5000`

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create .env file
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env

# 4. Run development server
npm start
```

Frontend will be available at `http://localhost:3000`

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# 1. Create .env file with your secrets
cp .env.example .env
nano .env  # Edit the file

# 2. Build and start containers
docker-compose up -d --build

# 3. Check logs
docker-compose logs -f backend

# 4. Stop containers
docker-compose down
```

### Individual Docker Commands

```bash
# Build the image
docker build -t secure-result-platform .

# Run with SQLite
docker run -p 5000:5000 secure-result-platform

# Run with PostgreSQL
docker run -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/dbname \
  -e SECRET_KEY=your-secret \
  -e JWT_SECRET_KEY=your-jwt-secret \
  secure-result-platform
```

---

## Cloud Deployment Options

### Azure App Service

#### Method 1: Using Azure CLI

```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name ResultPlatformRG --location eastus

# 3. Create PostgreSQL server
az postgres flexible-server create \
  --resource-group ResultPlatformRG \
  --name resultplatform-db \
  --location eastus \
  --admin-user sqladmin \
  --admin-password <YourPassword> \
  --sku-name Standard_B1ms

# 4. Create database
az postgres flexible-server db create \
  --resource-group ResultPlatformRG \
  --server-name resultplatform-db \
  --database-name results_db

# 5. Create App Service Plan
az appservice plan create \
  --name ResultPlatformPlan \
  --resource-group ResultPlatformRG \
  --sku B1 \
  --is-linux

# 6. Create Web App
az webapp create \
  --resource-group ResultPlatformRG \
  --plan ResultPlatformPlan \
  --name resultplatform-api \
  --runtime "PYTHON:3.11"

# 7. Configure environment variables
az webapp config appsettings set \
  --resource-group ResultPlatformRG \
  --name resultplatform-api \
  --settings \
    DATABASE_URL="postgresql://sqladmin:<password>@resultplatform-db.postgres.database.azure.com:5432/results_db" \
    SECRET_KEY="<your-secret>" \
    JWT_SECRET_KEY="<your-jwt-secret>"

# 8. Deploy from local Git
az webapp deployment source config-local-git \
  --name resultplatform-api \
  --resource-group ResultPlatformRG

# 9. Get deployment URL and push
git remote add azure <deployment-url>
git push azure main
```

#### Method 2: Using Docker Container

```bash
# 1. Build and push to Azure Container Registry
az acr create --resource-group ResultPlatformRG \
  --name resultplatformacr --sku Basic

az acr login --name resultplatformacr

docker build -t resultplatformacr.azurecr.io/backend:latest .
docker push resultplatformacr.azurecr.io/backend:latest

# 2. Create Web App from container
az webapp create \
  --resource-group ResultPlatformRG \
  --plan ResultPlatformPlan \
  --name resultplatform-api \
  --deployment-container-image-name resultplatformacr.azurecr.io/backend:latest
```

### AWS Elastic Beanstalk

```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Initialize EB application
eb init -p python-3.11 result-platform --region us-east-1

# 3. Create environment with PostgreSQL
eb create result-platform-env \
  --database.engine postgres \
  --database.username dbadmin \
  --database.password <YourPassword>

# 4. Set environment variables
eb setenv \
  SECRET_KEY="<your-secret>" \
  JWT_SECRET_KEY="<your-jwt-secret>"

# 5. Deploy
eb deploy

# 6. Open application
eb open
```

### Heroku

```bash
# 1. Login to Heroku
heroku login

# 2. Create application
heroku create result-platform-api

# 3. Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# 4. Set environment variables
heroku config:set SECRET_KEY="<your-secret>"
heroku config:set JWT_SECRET_KEY="<your-jwt-secret>"

# 5. Deploy
git push heroku main

# 6. Initialize database
heroku run python -c "from app import init_db; init_db()"

# 7. Open application
heroku open
```

#### Procfile for Heroku
Create a file named `Procfile`:
```
web: gunicorn app:app
release: python -c "from app import init_db; init_db()"
```

---

## Security Configuration

### 1. Generate Strong Secret Keys

```python
# Run this to generate secure keys
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(32))
print("JWT_SECRET_KEY:", secrets.token_urlsafe(32))
```

### 2. SSL/TLS Configuration (Nginx)

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:5000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            root /usr/share/nginx/html;
            try_files $uri /index.html;
        }
    }
}
```

### 3. Database Security

```sql
-- Create dedicated user for application
CREATE USER result_app WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE results_db TO result_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO result_app;

-- Enable SSL for database connections
-- In postgresql.conf:
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
```

### 4. Environment Security Checklist

- ✅ Change all default passwords
- ✅ Use strong, randomly generated SECRET_KEY and JWT_SECRET_KEY
- ✅ Enable HTTPS/SSL
- ✅ Set CORS origins to specific domains (not *)
- ✅ Use environment variables for all secrets
- ✅ Enable database SSL connections
- ✅ Implement rate limiting (consider Flask-Limiter)
- ✅ Regular security audits and updates

---

## Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:5000/api/health

# Login as admin
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin","password":"admin123","role":"admin"}'

# Save the token from response, then:
TOKEN="your-jwt-token-here"

# Upload result
curl -X POST http://localhost:5000/api/admin/results \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"matric":"STU001","subject":"Mathematics","score":85}'

# Get all results
curl -X GET http://localhost:5000/api/admin/results \
  -H "Authorization: Bearer $TOKEN"

# Get student results
curl -X GET http://localhost:5000/api/student/results/STU001 \
  -H "Authorization: Bearer $TOKEN"
```

### Using Postman

1. Import the API collection (create a Postman collection)
2. Set base URL: `{{base_url}}` = `http://localhost:5000/api`
3. Create environment variables for tokens
4. Test all endpoints

---

## Monitoring and Logging

### Application Logs

```bash
# Docker logs
docker-compose logs -f backend

# Heroku logs
heroku logs --tail

# Azure logs
az webapp log tail --name resultplatform-api --resource-group ResultPlatformRG
```

### Database Monitoring

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Monitor query performance
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

---

## Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test database connection
psql $DATABASE_URL
```

**CORS Errors**
- Update CORS_ORIGINS in .env
- Restart backend after changes

**JWT Token Issues**
- Ensure JWT_SECRET_KEY is set
- Check token expiration time
- Verify Authorization header format: `Bearer <token>`

**Port Already in Use**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

---

## Scaling Considerations

### Horizontal Scaling
- Deploy multiple backend instances behind load balancer
- Use managed database service (Azure Database, AWS RDS)
- Implement Redis for session caching

### Performance Optimization
- Enable database connection pooling
- Add caching layer (Redis/Memcached)
- Implement CDN for static assets
- Use database indexes on frequently queried fields

---

## Support

For issues and questions:
- Check the logs first
- Review environment variables
- Verify database connectivity
- Test with demo credentials

**Demo Credentials:**
- Admin: `admin` / `admin123`
- Student: `STU001` / `student123`