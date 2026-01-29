# Medical AI Backend

## Overview
FastAPI backend for the Medical AI application with authentication, user management, and health prediction services.

## Essential Files Structure
```
backend/
├── main.py              # Main FastAPI application
├── database.py          # MongoDB database connection
├── dependencies.py      # Authentication dependencies
├── auth_utils.py        # JWT token utilities
├── .env                 # Environment variables (NOT tracked)
├── .gitignore           # Git ignore rules
└── routes/              # API route handlers
    ├── auth.py          # Authentication endpoints
    ├── user_dashboard.py # User dashboard endpoints
    ├── admin_dashboard.py # Admin dashboard endpoints
    ├── prediction.py    # Health prediction endpoints
    ├── chat.py          # AI chat endpoints
    └── voice_assistant.py # Voice assistant endpoints
```

## Model Files
Large ML model files (*.pkl) are stored locally but NOT tracked in Git to keep repository size small:
- `alzheimer_model.pkl` (~1.7MB)
- `heart_disease_model.pkl` (~786KB) 
- `hybrid_alzheimer_model.pkl` (~5.3MB)
- `hybrid_heart_model.pkl` (~1.8MB)

For deployment, these model files should be:
1. Uploaded to cloud storage (AWS S3, Google Cloud Storage, etc.)
2. Downloaded during deployment setup
3. Or included in deployment package separately

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `.\venv\Scripts\Activate.ps1` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables in `.env`
5. Run: `uvicorn main:app --reload --port 8000`

## Environment Variables
Required variables in `.env`:
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `JWT_SECRET`: JWT secret key

## API Endpoints
- Authentication: `/auth/login`, `/auth/register`
- User Dashboard: `/dashboard/user/*`
- Admin Dashboard: `/admin/*`
- Predictions: `/predict/*`
- Chat: `/chat/*`
- Voice Assistant: `/voice/*`
