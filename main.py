from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.admin_dashboard import router as admin_router

from routes import auth, prediction, voice_assistant, chat, user_dashboard
from routes import notifications

app = FastAPI(title="Medical AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    expose_headers=["Content-Type", "Content-Disposition"],
)

# Existing routers (UNCHANGED)
app.include_router(auth.router, prefix="/auth")
app.include_router(prediction.router, prefix="/predict")
app.include_router(voice_assistant.router)
app.include_router(chat.router)
app.include_router(user_dashboard.router, prefix="/dashboard")
app.include_router(admin_router)
app.include_router(notifications.router)


# ✅ Missing Admin Router (THIS fixes everything)
#app.include_router(admin_dashboard.router, prefix="/dashboard")

@app.get("/")
def root():
    return {"status": "Medical AI Backend Running"}
