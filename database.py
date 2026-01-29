import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URL or not DB_NAME:
    raise RuntimeError("Missing DB config")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

users_col = db["users"]
predictions_col = db["predictions"]
reports_col = db["reports"]
chat_col = db["chat_history"]

def col(name: str):
    return db[name]
