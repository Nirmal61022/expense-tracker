import os
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Fallback in-memory stores in case MongoDB is not yet provisioned or temporarily unreachable
FALLBACK_CHAT_LOGS = []
FALLBACK_CHAT_FEEDBACK = []

_client = None
_db = None


def get_mongo_db():
    global _client, _db
    if _db is not None:
        return _db

    mongo_uri = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')
    if not mongo_uri:
        logger.debug("MONGODB_URI not configured; using fallback in-memory log store.")
        return None

    try:
        _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        # Ping the server to verify connection
        _client.admin.command('ping')
        # Extract database name or default to 'expensetracker'
        db_name = os.environ.get('MONGODB_DB_NAME', 'expensetracker')
        _db = _client[db_name]
        logger.info(f"Successfully connected to MongoDB database: {db_name}")
        return _db
    except (PyMongoError, ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"Could not connect to MongoDB ({e}); falling back to safe local store.")
        _client = None
        _db = None
        return None


def log_chat_interaction(session_id, user_message, bot_response, intent='general', user_id=None, metadata=None):
    """
    Log a chat message exchange into MongoDB collection 'chat_logs'.
    Falls back gracefully if MongoDB is unreachable.
    """
    record = {
        'session_id': session_id,
        'user_id': user_id,
        'user_message': user_message,
        'bot_response': bot_response,
        'intent': intent,
        'metadata': metadata or {},
        'created_at': datetime.utcnow(),
    }

    db = get_mongo_db()
    if db is not None:
        try:
            res = db.chat_logs.insert_one(record)
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert chat log into MongoDB: {e}")

    # Fallback storage
    FALLBACK_CHAT_LOGS.append(record)
    return f"fallback-{len(FALLBACK_CHAT_LOGS)}"


def log_chat_feedback(session_id, rating, comments='', user_id=None):
    """
    Log user feedback on chat responses into MongoDB collection 'chat_feedback'.
    """
    record = {
        'session_id': session_id,
        'user_id': user_id,
        'rating': rating,  # 1 (thumbs up), -1 (thumbs down)
        'comments': comments,
        'created_at': datetime.utcnow(),
    }

    db = get_mongo_db()
    if db is not None:
        try:
            res = db.chat_feedback.insert_one(record)
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert feedback into MongoDB: {e}")

    FALLBACK_CHAT_FEEDBACK.append(record)
    return f"fallback-{len(FALLBACK_CHAT_FEEDBACK)}"


def check_mongo_health():
    """
    Returns connection status and ping latency for the health check endpoint.
    """
    mongo_uri = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')
    if not mongo_uri:
        return {'status': 'not_configured', 'mode': 'fallback_in_memory'}

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
        client.admin.command('ping')
        return {'status': 'connected', 'mode': 'mongodb'}
    except Exception as e:
        return {'status': 'disconnected', 'error': str(e), 'mode': 'fallback_in_memory'}
