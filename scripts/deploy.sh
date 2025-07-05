#!/bin/bash

# deploy.sh - Deployment script for Phone Call Assistant

set -e

echo "----------------------------------------"
echo "🚀 Phone Call Assistant Deployment Script"
echo "----------------------------------------"

# 1. Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"
if [[ $(echo -e "$PYTHON_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) != "$REQUIRED_VERSION" ]]; then
  echo "Python 3.9+ is required. Current version: $PYTHON_VERSION"
  exit 1
fi

# 2. Create virtual environment if not exists
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# 3. Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# 4. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# 5. Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 6. Copy .env.example to .env if .env does not exist
if [ ! -f "config/.env" ]; then
  echo "Setting up environment variables..."
  cp config/.env.example config/.env
  echo "Please edit config/.env with your API keys and settings."
fi

# 7. Initialize database (if setup_db.py exists)
if [ -f "scripts/setup_db.py" ]; then
  echo "Initializing database..."
  python scripts/setup_db.py --create
fi

# 8. Run migrations (if using Alembic or similar)
if [ -d "migrations" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

echo "----------------------------------------"
echo "✅ Setup complete!"
echo ""

# 9. Start the FastAPI server
echo "Starting the FastAPI server..."
uvicorn app.main:app --reload

# End of script
