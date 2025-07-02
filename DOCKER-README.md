# 🐳 Docker Development Setup

This guide helps you set up the AI Trip Planner using Docker for local development.

## 📋 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git (to clone the repository)

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
cd ai-trip-planner
scripts\dev-setup.bat
```

**Mac/Linux:**
```bash
cd ai-trip-planner
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh
```

### Option 2: Manual Setup

1. **Copy environment variables:**
   ```bash
   cp .env .env.docker
   # Edit .env.docker with your API keys
   ```

2. **Start the development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

## 🌐 Access Points

Once running, you can access:

- **Frontend (Next.js):** http://localhost:3000
- **Backend (FastAPI):** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **MongoDB Admin UI:** http://localhost:8081

## 📂 Project Structure

```
ai-trip-planner/
├── frontend/
│   ├── Dockerfile.dev       # Frontend development container
│   └── .dockerignore
├── backend/
│   ├── Dockerfile.dev       # Backend development container
│   └── .dockerignore
├── docker-compose.dev.yml   # Development services
├── .env.docker             # Docker environment variables
└── scripts/
    ├── dev-setup.bat       # Windows setup script
    ├── dev-setup.sh        # Mac/Linux setup script
    └── init-mongo.js       # MongoDB initialization
```

## 🔧 Common Commands

### Start/Stop Services
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Stop all services
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# View specific service logs
docker-compose -f docker-compose.dev.yml logs -f frontend
docker-compose -f docker-compose.dev.yml logs -f backend
```

### Development Workflow
```bash
# Rebuild containers after code changes
docker-compose -f docker-compose.dev.yml build

# Force rebuild (no cache)
docker-compose -f docker-compose.dev.yml build --no-cache

# Restart a specific service
docker-compose -f docker-compose.dev.yml restart backend

# Execute commands in running containers
docker-compose -f docker-compose.dev.yml exec backend bash
docker-compose -f docker-compose.dev.yml exec frontend sh
```

### Database Management
```bash
# Reset database (removes all data)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d

# Backup database
docker-compose -f docker-compose.dev.yml exec mongodb mongodump --out /data/backup

# Access MongoDB shell
docker-compose -f docker-compose.dev.yml exec mongodb mongosh -u admin -p password123
```

## 🔍 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using the port
netstat -an | findstr :3000  # Windows
lsof -i :3000               # Mac/Linux

# Kill the process or change the port in docker-compose.dev.yml
```

**Container won't start:**
```bash
# Check logs for errors
docker-compose -f docker-compose.dev.yml logs [service-name]

# Rebuild without cache
docker-compose -f docker-compose.dev.yml build --no-cache
```

**Changes not reflecting:**
- Frontend: Should auto-reload (check WATCHPACK_POLLING=true)
- Backend: Should auto-reload with --reload flag
- If not working, restart the specific service

**Database connection issues:**
```bash
# Check if MongoDB is running
docker-compose -f docker-compose.dev.yml ps

# Check database logs
docker-compose -f docker-compose.dev.yml logs mongodb
```

## 🔧 Environment Variables

Update `.env.docker` with your actual API keys:

```env
GOOGLE_API_KEY=your_actual_google_api_key
AMADEUS_API_KEY=your_actual_amadeus_key
AMADEUS_API_SECRET=your_actual_amadeus_secret
SERPAPI_API_KEY=your_actual_serpapi_key
```

## 🚀 Production Deployment

For production deployment, continue using your current setup:
- Frontend: Vercel
- Backend: Render
- Database: MongoDB Atlas

This Docker setup is optimized for local development only.

## 📝 Notes

- The frontend runs on `http://localhost:3000` with hot reload
- The backend runs on `http://localhost:8000` with auto-reload
- MongoDB data persists in Docker volumes
- Code changes are automatically reflected (volume mounts)
