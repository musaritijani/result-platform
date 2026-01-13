# Secure Result Computation Platform

A cloud-based academic result management system with TEE (Trusted Execution Environment) enhanced security principles. Built with Flask (Python) backend and React frontend.

## 🎯 Project Overview

This platform addresses critical security challenges in cloud-based result computation:
- **Unauthorized Access**: JWT-based authentication with role-based access control
- **Data Tampering**: Backend validation and integrity checks
- **Result Manipulation**: Simulated TEE principles for secure computation
- **Audit Trail**: Complete logging of all operations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  - Landing Page  - Login  - Admin Dashboard  - Student View │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS/JWT
┌────────────────────────────▼────────────────────────────────┐
│                   Backend (Flask API)                       │
│  - Authentication  - Role-Based Access  - Result Management │
└────────────────────────────┬────────────────────────────────┘
                             │ SQL
┌────────────────────────────▼────────────────────────────────┐
│              Database (PostgreSQL/SQLite)                   │
│  - Admin  - Student  - Results  - Audit Logs               │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

### Admin Features
- ✅ Secure login with JWT authentication
- ✅ Register new students
- ✅ Upload student results (matric, subject, score)
- ✅ View all results in tabular format
- ✅ Update existing results
- ✅ Delete results
- ✅ Audit trail of all actions

### Student Features
- ✅ Secure login with matric number
- ✅ View personal results
- ✅ Search by matric number
- ✅ Grade calculation (A-F)
- ✅ Read-only access to own data

### Security Features
- 🔒 Password hashing (Werkzeug)
- 🔑 JWT token-based authentication
- 🛡️ Role-based access control (RBAC)
- 📝 Comprehensive audit logging
- ✔️ Input validation and sanitization
- 🔐 CORS protection
- 🚫 SQL injection prevention (SQLAlchemy ORM)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+ (for frontend)
- PostgreSQL (optional, SQLite works for development)
- Docker (optional)

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd secure-result-platform

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Start the server
python app.py
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 4. Initialize database
python -c "from app import init_db; init_db()"

# 5. Run application
python app.py
```

### Option 3: Docker

```bash
# Start all services (backend + database)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📁 Project Structure

```
secure-result-platform/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Multi-container setup
├── .env.example           # Environment variables template
├── setup.sh               # Automated setup script
├── test_api.py            # Automated tests
├── DEPLOYMENT_GUIDE.md    # Detailed deployment instructions
├── README.md              # This file
└── frontend/              # React frontend (artifact)
    ├── public/
    └── src/
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following:

```bash
# Flask Configuration
SECRET_KEY=your-random-secret-key
JWT_SECRET_KEY=your-random-jwt-key
FLASK_ENV=production

# Database (choose one)
DATABASE_URL=sqlite:///results.db  # Development
# DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Production

# Security
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

Generate secure keys:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## 📡 API Endpoints

### Authentication
```
POST /api/auth/login              # Login (admin/student)
POST /api/auth/register-admin     # Register admin (protected)
```

### Admin Endpoints (Requires Admin JWT)
```
POST   /api/admin/students        # Register student
POST   /api/admin/results         # Upload result
GET    /api/admin/results         # Get all results
PUT    /api/admin/results/:id     # Update result
DELETE /api/admin/results/:id     # Delete result
```

### Student Endpoints (Requires Student JWT)
```
GET /api/student/results/:matric  # Get student results
```

### Public Endpoints
```
GET /api/health                   # Health check
GET /                             # API info
```

## 🧪 Testing

### Run Automated Tests
```bash
# Install pytest
pip install pytest

# Run all tests
pytest test_api.py -v

# Run specific test
pytest test_api.py::test_admin_login_success -v

# Run with coverage
pytest test_api.py --cov=app
```

### Manual Testing with cURL

```bash
# 1. Health check
curl http://localhost:5000/api/health

# 2. Login as admin
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin","password":"admin123","role":"admin"}'

# Save the token, then:

# 3. Upload result
curl -X POST http://localhost:5000/api/admin/results \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"matric":"STU001","subject":"Mathematics","score":85}'

# 4. Get all results
curl -X GET http://localhost:5000/api/admin/results \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🌐 Deployment

### Cloud Platforms

#### Heroku
```bash
heroku create result-platform-api
heroku addons:create heroku-postgresql:mini
git push heroku main
```

#### Azure
```bash
az webapp up --name result-platform --runtime "PYTHON:3.11"
```

#### AWS Elastic Beanstalk
```bash
eb init -p python-3.11 result-platform
eb create result-platform-env
eb deploy
```

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.**

## 🔐 Security Best Practices

### In Production
- [ ] Change all default passwords
- [ ] Use strong, randomly generated secret keys
- [ ] Enable HTTPS/SSL
- [ ] Set specific CORS origins (not *)
- [ ] Use environment variables for all secrets
- [ ] Enable database SSL connections
- [ ] Implement rate limiting
- [ ] Regular security audits
- [ ] Keep dependencies updated
- [ ] Enable database backups

### Default Credentials (CHANGE IN PRODUCTION!)
```
Admin:
  Username: admin
  Password: admin123

Student:
  Matric:   STU001
  Password: student123
```

## 📊 Database Schema

### Tables

**admins**
- id (PK)
- username (unique)
- email (unique)
- password_hash

**students**
- id (PK)
- name
- matric (unique)
- email (unique)
- password_hash

**results**
- id (PK)
- matric (FK → students.matric)
- subject
- score
- created_at
- updated_at

**audit_logs**
- id (PK)
- user_type (admin/student)
- user_id
- action
- details
- timestamp

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

**2. ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**3. Port Already in Use**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

**4. JWT Token Expired**
```bash
# Login again to get new token
# Or increase JWT_ACCESS_TOKEN_EXPIRES in app.py
```

## 📈 Performance Optimization

- Use connection pooling for database
- Implement Redis caching for frequent queries
- Add indexes on matric and subject columns
- Use CDN for static assets
- Enable gzip compression
- Deploy multiple instances with load balancer

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is created for educational purposes as part of a university project on Trusted Execution Environments in Cloud Computing.

## 🙏 Acknowledgments

- Flask framework for robust backend
- React for interactive frontend
- SQLAlchemy for database management
- Intel SGX SDK documentation for TEE concepts
- JWT for secure authentication

## 📞 Support

For issues:
1. Check the logs (`docker-compose logs -f backend`)
2. Review environment variables
3. Test with demo credentials
4. Consult DEPLOYMENT_GUIDE.md

## 🎓 Research Context

This project implements concepts from the research paper:
**"Enhancing Security and Integrity of Results Computation in Cloud Computing Using Trusted Execution Environment (TEE) Technique"**

Key implementations:
- ✅ Simulated TEE isolation through backend validation
- ✅ Encrypted token-based access control
- ✅ Integrity assurance through audit logging
- ✅ Cloud-ready architecture (Docker, PostgreSQL)
- ✅ Multi-role authentication (Admin/Student)

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Status:** Production Ready ✅