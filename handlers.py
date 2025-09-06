import config
import db
import utils
import drive_client
import requests

# ---------- Start / Help ----------
def handle_start(chat_id):
    utils.send_message(chat_id, "Hi, I’m Jessica 🤖, your academic assistant for ECE notes!\nUse /help to see what I can do.")

def handle_help(chat_id):
    utils.send_message(chat_id,
        "Here’s what I can do:\n"
        "/subject CODE - Get notes for a subject\n"
        "/upload CODE - Upload a note (PDF or YouTube link)\n"
        "/pending - Show pending notes (Admin only)\n"
        "/approve ID - Approve a note (Admin only)\n"
        "/reject ID - Reject a note (Admin only)"
    )

# ---------- Subject ----------
def handle_subject(chat_id, code):
    notes = db.get_notes(code)
    if not notes:
        utils.send_message(chat_id, f"No approved notes yet for {code}.")
    else:
        msg = f"📚 Notes for {code}:\n"
        for n in notes:
            msg += f"- {n['type'].upper()}: {n['link']}\n"
        utils.send_message(chat_id, msg)

# ---------- Upload ----------
def handle_upload(chat_id, code, document=None, link=None):
    if document:  # PDF file upload
        file_id = document["file_id"]
        file_path = get_file_path(file_id)
        file_bytes = download_file(file_path)
        drive_link = drive_client.upload_file(file_bytes, document["file_name"])
        note_id = db.add_note(code, drive_link, "pdf", chat_id,
                              "approved" if config.AUTO_APPROVE else "pending")
        utils.send_message(chat_id, f"📄 PDF submitted. ID: {note_id}")
    elif link:  # YouTube link directly
        note_id = db.add_note(code, link, "youtube", chat_id,
                              "approved" if config.AUTO_APPROVE else "pending")
        utils.send_message(chat_id, f"🎥 Video link submitted. ID: {note_id}")
    else:
        # Remember this chat is waiting for next message
        db.set_session(chat_id, code)
        utils.send_message(chat_id, f"Upload session started for {code}. Now send me a PDF file or YouTube link.")

def handle_followup(chat_id, text=None, document=None):
    subject_code = db.get_session(chat_id)
    if not subject_code:
        return False

    if document:  # File upload
        file_id = document["file_id"]
        file_path = get_file_path(file_id)
        file_bytes = download_file(file_path)
        drive_link = drive_client.upload_file(file_bytes, document["file_name"])
        note_id = db.add_note(subject_code, drive_link, "pdf", chat_id,
                              "approved" if config.AUTO_APPROVE else "pending")
        utils.send_message(chat_id, f"📄 PDF submitted. ID: {note_id}")
        db.clear_session(chat_id)
        return True

    if text and ("youtu" in text or "http" in text):  # Link upload
        note_id = db.add_note(subject_code, text, "youtube", chat_id,
                              "approved" if config.AUTO_APPROVE else "pending")
        utils.send_message(chat_id, f"🎥 Video link submitted. ID: {note_id}")
        db.clear_session(chat_id)
        return True

    return False

# ---------- Admin ----------
def handle_pending(chat_id):
    if chat_id not in config.ADMIN_IDS:
        utils.send_message(chat_id, "❌ Not authorized.")
        return
    notes = db.list_pending()
    if not notes:
        utils.send_message(chat_id, "✅ No pending notes.")
    else:
        msg = "⏳ Pending notes:\n"
        for n in notes:
            msg += f"{n['_id']} | {n['subject_code']} | {n['type']}\n"
        utils.send_message(chat_id, msg)

def handle_approve(chat_id, note_id):
    if chat_id not in config.ADMIN_IDS:
        utils.send_message(chat_id, "❌ Not authorized.")
        return
    db.approve(note_id)
    utils.send_message(chat_id, f"✅ Note {note_id} approved.")

def handle_reject(chat_id, note_id):
    if chat_id not in config.ADMIN_IDS:
        utils.send_message(chat_id, "❌ Not authorized.")
        return
    db.reject(note_id)
    utils.send_message(chat_id, f"❌ Note {note_id} rejected.")

# ---------- File Helpers ----------
def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    resp = requests.get(url).json()
    return resp["result"]["file_path"]

def download_file(file_path):
    url = f"https://api.telegram.org/file/bot{config.TELEGRAM_TOKEN}/{file_path}"
    resp = requests.get(url)
    return resp.content
