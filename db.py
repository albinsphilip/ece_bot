from pymongo import MongoClient
from bson import ObjectId
import config

client = MongoClient(config.MONGO_URI)
# Prefer default DB from URI; fallback to named DB
try:
    db = client.get_default_database()
except Exception:
    db = client[config.DB_NAME]

subjects_col = db["subjects"]
notes_col = db["notes"]
sessions_col = db["sessions"]
syllabus_col = db["syllabus"]
pyq_col = db["pyqs"]
playlist_col = db["playlists"]
jobs_col = db["jobs"]

# ---------- Subjects ----------
def add_subject(code: str, name: str, semester: int, credits: int):
    subjects_col.update_one(
        {"code": code},
        {"$set": {"name": name, "semester": semester, "credits": credits}},
        upsert=True
    )

def list_subjects():
    return list(subjects_col.find({}))

def get_subjects_by_semester(sem: int):
    return list(subjects_col.find({"semester": sem}))

def get_subject(code: str):
    return subjects_col.find_one({"code": code})

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

# ---------- Syllabus ----------
def set_syllabus(sem: int, link: str):
    syllabus_col.update_one({"semester": sem}, {"$set": {"link": link}}, upsert=True)

def get_syllabus(sem: int):
    return syllabus_col.find_one({"semester": sem})

# ---------- PYQs ----------
def add_pyq(subject_code: str, year: int, link: str):
    pyq_col.insert_one({"subject_code": subject_code, "year": year, "link": link})

def get_pyqs(subject_code: str):
    return list(pyq_col.find({"subject_code": subject_code}))

# ---------- Playlists ----------
def add_playlist(subject_code: str, title: str, link: str):
    playlist_col.insert_one({"subject_code": subject_code, "title": title, "link": link})

def get_playlists(subject_code: str):
    return list(playlist_col.find({"subject_code": subject_code}))

# ---------- Jobs (background processing) ----------
def create_job(job: dict) -> str:
    result = jobs_col.insert_one(job)
    return str(result.inserted_id)

def get_job(job_id: str):
    return jobs_col.find_one({"_id": ObjectId(job_id)})

def set_job_status(job_id: str, status: str, extra: dict = None):
    update = {"status": status}
    if extra:
        update.update(extra)
    jobs_col.update_one({"_id": ObjectId(job_id)}, {"$set": update})
