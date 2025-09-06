from pymongo import MongoClient
from bson import ObjectId
import config

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]

subjects_col = db["subjects"]
notes_col = db["notes"]

def add_subject(code: str, name: str):
    subjects_col.update_one({"code": code}, {"$set": {"name": name}}, upsert=True)

def list_subjects():
    return list(subjects_col.find({}))

def add_note(subject_code: str, link: str, note_type: str, uploader: int, status="pending"):
    note = {
        "subject_code": subject_code,
        "link": link,
        "type": note_type,
        "uploader": uploader,
        "status": status
    }
    result = notes_col.insert_one(note)
    return str(result.inserted_id)

def get_notes(subject_code: str):
    return list(notes_col.find({"subject_code": subject_code, "status": "approved"}))

def list_pending():
    return list(notes_col.find({"status": "pending"}))

def approve(note_id: str):
    return notes_col.update_one({"_id": ObjectId(note_id)}, {"$set": {"status": "approved"}})

def reject(note_id: str):
    return notes_col.update_one({"_id": ObjectId(note_id)}, {"$set": {"status": "rejected"}})
