from pymongo import MongoClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: MongoClient = None
    db = None

db_instance = MongoDB()

def get_db():
    if db_instance.db is None:
        try:
            db_instance.client = MongoClient(settings.MONGODB_URI)
            db_instance.db = db_instance.client[settings.MONGODB_DATABASE]
            logger.info(f"Connected to MongoDB database: {settings.MONGODB_DATABASE}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e
    return db_instance.db

def get_collection(name: str):
    db = get_db()
    return db[name]
