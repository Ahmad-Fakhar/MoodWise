import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "fastauth_notes")

client: AsyncIOMotorClient = None
database = None

async def get_database():
    return database

async def connect_to_mongo():
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    print(f"✅ Connected to MongoDB at {MONGODB_URL}")

    # Create indexes
    await database.users.create_index("email", unique=True)
    await database.users.create_index("username")
    await database.notes.create_index("user_id")
    await database.password_resets.create_index("token", unique=True)
    await database.password_resets.create_index("expires_at")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❌ Disconnected from MongoDB")
