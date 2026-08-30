import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hyperforge")

client = None
db = None

async def init_db():
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
        db = client[DB_NAME]
        await client.server_info()
        print("Connected to MongoDB successfully.")
    except Exception as e:
        print(f"MongoDB connection warning: {e}. Running in memory-safe mode if needed.")
        db = client[DB_NAME]

def get_db():
    global db
    if db is None:
        client_init = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
        db = client_init[DB_NAME]
    return db
