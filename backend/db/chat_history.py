from backend.db.mongo_client import db
from datetime import datetime

chat_col = db["chat_history"]

def save_message(user_id, role, message):
    chat_col.insert_one({
        "user_id": user_id,
        "role": role,
        "message": message,
        "timestamp": datetime.utcnow()
    })

def load_history(user_id):
    return list(chat_col.find({"user_id": user_id}).sort("timestamp", 1))
