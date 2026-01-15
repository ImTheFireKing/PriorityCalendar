from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("mongoConString")
try:
    client = MongoClient(uri)
    client.admin.command("ping")
    print("Connected successfully")
except Exception as e:
    print(e)