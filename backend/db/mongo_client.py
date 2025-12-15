from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["vietnam_ai"]
tourism = db["tourism"]
