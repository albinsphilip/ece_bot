from pymongo import MongoClient
from bson import ObjectId
import config

client = MongoClient(config.MONGO_URI)
db = client.get_default_database()

subjects_col = db["subjects"]
notes_col = db["notes"]
sessions_col = db["sessions"]

# ---------- Subjects ----------
def add_subject(code: str, name: str):
    subjects_col.update_one({"code": code}, {"$set": {"name": name}}, upsert=True)

def list_subjects():
    return list(subjects_col.find({}))

# ---------- Notes ----------
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

# ---------- Upload Sessions ----------
def set_session(user_id, subject_code):
    sessions_col.update_one(
        {"user_id": user_id},
        {"$set": {"subject_code": subject_code}},
        upsert=True
    )

def get_session(user_id):
    doc = sessions_col.find_one({"user_id": user_id})
    return doc["subject_code"] if doc else None

def clear_session(user_id):
    sessions_col.delete_one({"user_id": user_id})
