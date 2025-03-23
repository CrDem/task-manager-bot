from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["task_manager"]
tasks_collection = db["tasks"]
user_states_collection = db["user_states"]
