#!/bin/bash

# Secure Result Platform - Quick Setup Script
# This script automates the setup process for local development

set -e  # Exit on error

echo "======================================"
echo "Secure Result Platform - Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.10+ required. You have Python $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version compatible ($PYTHON_VERSION)${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo -e "${RED}Error: Could not activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment created and activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate random secret keys
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env with generated keys
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|your-super-secret-key-change-in-production-use-random-string|$SECRET_KEY|g" .env
        sed -i '' "s|your-jwt-secret-key-change-in-production-use-random-string|$JWT_SECRET|g" .env
    else
        # Linux
        sed -i "s|your-super-secret-key-change-in-production-use-random-string|$SECRET_KEY|g" .env
        sed -i "s|your-jwt-secret-key-change-in-production-use-random-string|$JWT_SECRET|g" .env
    fi
    
    echo -e "${GREEN}✓ .env file created with secure keys${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping...${NC}"
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from app import init_db; init_db()"

echo -e "${GREEN}✓ Database initialized${NC}"

# Check if Docker is installed (optional)
echo ""
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker found (optional)${NC}"
    
    # Ask if user wants to use Docker
    read -p "Do you want to set up Docker containers? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f docker-compose.yml ]; then
            echo "Building Docker containers..."
            docker-compose build
            echo -e "${GREEN}✓ Docker containers built${NC}"
            echo ""
            echo -e "${YELLOW}To start containers, run: docker-compose up -d${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ Docker not found (optional for deployment)${NC}"
fi

# Display success message and next steps
echo ""
echo "======================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend server:"
echo -e "   ${YELLOW}python app.py${NC}"
echo "   or"
echo -e "   ${YELLOW}gunicorn --bind 0.0.0.0:5000 app:app${NC}"
echo ""
echo "2. Access the API at:"
echo -e "   ${YELLOW}http://localhost:5000${NC}"
echo ""
echo "3. Test the API:"
echo -e "   ${YELLOW}curl http://localhost:5000/api/health${NC}"
echo ""
echo "4. Run tests:"
echo -e "   ${YELLOW}pytest test_api.py -v${NC}"
echo ""
echo "Default credentials:"
echo -e "   Admin    - Username: ${YELLOW}admin${NC}     Password: ${YELLOW}admin123${NC}"
echo -e "   Student  - Matric:   ${YELLOW}STU001${NC}    Password: ${YELLOW}student123${NC}"
echo ""
echo "For deployment instructions, see DEPLOYMENT_GUIDE.md"
echo ""