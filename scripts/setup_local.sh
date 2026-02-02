#!/bin/bash

# ============================================
# MeetMate Local Development Setup
# ============================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
INFRA_DIR="$PROJECT_ROOT/infra"

echo "🚀 MeetMate Local Development Setup"
echo "===================================="
echo ""

# Step 1: Check Docker
echo "📦 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"
echo ""

# Step 2: Start PostgreSQL with Docker
echo "🗄️  Starting PostgreSQL database..."
cd "$INFRA_DIR"
docker-compose up -d postgres
echo "✅ PostgreSQL started on port 5433"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
until docker exec vnpt_meetmate_db pg_isready -U meetmate > /dev/null 2>&1; do
    echo "   Waiting..."
    sleep 2
done
echo "✅ PostgreSQL is ready"
echo ""

# Step 3: Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Created new virtual environment"
fi

source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Step 4: Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Step 5: Create .env.local if not exists
ENV_FILE="$BACKEND_DIR/.env.local"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating .env.local..."
    cat > "$ENV_FILE" << EOF
# MeetMate Local Environment
ENV=development
DATABASE_URL=postgresql+psycopg2://meetmate:meetmate@localhost:5433/meetmate
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=*

# AI Keys (optional for local testing)
GEMINI_API_KEY=
OPENAI_API_KEY=
EOF
    echo "✅ Created .env.local"
else
    echo "✅ .env.local already exists"
fi
echo ""

# Step 6: Show summary
echo "===================================="
echo "🎉 Setup Complete!"
echo "===================================="
echo ""
echo "📌 Database:"
echo "   Host: localhost"
echo "   Port: 5433"
echo "   User: meetmate"
echo "   Password: meetmate"
echo "   Database: meetmate"
echo ""
echo "📌 To start backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload --port 8000"
echo ""
echo "📌 API will be available at:"
echo "   http://localhost:8000"
echo "   http://localhost:8000/docs (Swagger UI)"
echo ""
echo "📌 Demo login:"
echo "   Email: nguyenvana@lpbank.vn"
echo "   Password: demo123"
echo ""
echo "📌 To stop database:"
echo "   cd infra && docker-compose down"
echo ""

