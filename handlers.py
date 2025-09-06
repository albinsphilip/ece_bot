import config
import db
import utils
import requests

# University grade point mapping (example)
GRADE_POINTS = {
    "O": 10,
    "A+": 9,
    "A": 8.5,
    "B+": 8,
    "B": 7,
    "C": 6,
    "P": 5,
    "F": 0
}

# ---------- Start / Help ----------
def handle_start(chat_id):
    utils.send_message(chat_id, "Hi, I’m Jessica 🤖, your academic assistant for ECE notes!\nUse /help to see what I can do.")

def handle_help(chat_id):
    utils.send_message(chat_id,
        "Here’s what I can do:\n"
        "/semester N - List subjects in a semester\n"
        "/syllabus N - Get syllabus for semester\n"
        "/subject CODE - Get approved notes\n"
        "/pyq CODE - Get past year papers\n"
        "/playlist CODE - Recommended YouTube playlists\n"
        "/upload CODE [LINK] - Upload a PDF (send file) or a YouTube link\n"
        "/gpa sgpa <SEM> <grades...>\n"
        "/gpa cgpa <SGPA1> <SGPA2> ... (up to your current sem)\n"
        "/pending - Show pending notes (Admin)\n"
        "/approve ID - Approve note (Admin)\n"
        "/reject ID - Reject note (Admin)"
    )

# ---------- Subjects ----------
def handle_semester(chat_id, sem):
    try:
        sem = int(sem)
    except ValueError:
        utils.send_message(chat_id, "Semester must be a number.")
        return
    subjects = db.get_subjects_by_semester(sem)
    if not subjects:
        utils.send_message(chat_id, f"No subjects found for semester {sem}.")
    else:
        msg = f"📘 Subjects in Semester {sem}:\n"
        for s in subjects:
            msg += f"- {s['code']}: {s['name']} ({s.get('credits', 0)} credits)\n"
        utils.send_message(chat_id, msg)

def handle_subject(chat_id, code):
    notes = db.get_notes(code)
    if not notes:
        utils.send_message(chat_id, f"No approved notes yet for {code}.")
    else:
        msg = f"📚 Notes for {code}:\n"
        for n in notes:
            msg += f"- {n['type'].upper()}: {n['link']}\n"
        utils.send_message(chat_id, msg)

# ---------- Upload (job-based) ----------
def handle_upload(chat_id, code, document=None, link=None):
    """
    If document is present, create a PDF job.
    If link is provided (in same message), create a YouTube job.
    If neither, start a session and prompt user to send file/link.
    """
    if document:
        # Queue a PDF job
        job_id = db.create_job({
            "type": "pdf",
            "status": "queued",
            "chat_id": chat_id,
            "subject_code": code,
            "telegram_file_id": document["file_id"],
            "original_filename": document.get("file_name", "note.pdf")
        })
        utils.send_message(chat_id, f"⏳ Processing your PDF for {code}... I’ll notify you when it’s ready. (Job {job_id})")
        utils.trigger_worker(job_id)
        return

    if link:
        job_id = db.create_job({
            "type": "youtube",
            "status": "queued",
            "chat_id": chat_id,
            "subject_code": code,
            "link": link
        })
        utils.send_message(chat_id, f"⏳ Processing your link for {code}... I’ll notify you when it’s ready. (Job {job_id})")
        utils.trigger_worker(job_id)
        return

    # Neither provided: start session
    db.set_session(chat_id, code)
    utils.send_message(chat_id, f"Upload session started for {code}. Now send me a PDF file or a YouTube link.")

def handle_followup(chat_id, text=None, document=None):
    subject_code = db.get_session(chat_id)
    if not subject_code:
        return False

    if document:
        job_id = db.create_job({
            "type": "pdf",
            "status": "queued",
            "chat_id": chat_id,
            "subject_code": subject_code,
            "telegram_file_id": document["file_id"],
            "original_filename": document.get("file_name", "note.pdf")
        })
        utils.send_message(chat_id, f"⏳ Processing your PDF for {subject_code}... I’ll notify you when it’s ready. (Job {job_id})")
        db.clear_session(chat_id)
        utils.trigger_worker(job_id)
        return True

    if text and ("youtu" in text or "http" in text):
        job_id = db.create_job({
            "type": "youtube",
            "status": "queued",
            "chat_id": chat_id,
            "subject_code": subject_code,
            "link": text
        })
        utils.send_message(chat_id, f"⏳ Processing your link for {subject_code}... I’ll notify you when it’s ready. (Job {job_id})")
        db.clear_session(chat_id)
        utils.trigger_worker(job_id)
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

# ---------- Syllabus ----------
def handle_syllabus(chat_id, sem):
    try:
        sem = int(sem)
    except ValueError:
        utils.send_message(chat_id, "Semester must be a number.")
        return
    doc = db.get_syllabus(sem)
    if not doc:
        utils.send_message(chat_id, f"No syllabus found for semester {sem}.")
    else:
        utils.send_message(chat_id, f"📑 Syllabus for Semester {sem}: {doc['link']}")

# ---------- PYQs ----------
def handle_pyq(chat_id, code):
    pyqs = db.get_pyqs(code)
    if not pyqs:
        utils.send_message(chat_id, f"No question papers found for {code}.")
    else:
        msg = f"📂 Previous Year Question Papers for {code}:\n"
        for p in pyqs:
            msg += f"- {p['year']}: {p['link']}\n"
        utils.send_message(chat_id, msg)

# ---------- Playlists ----------
def handle_playlist(chat_id, code):
    playlists = db.get_playlists(code)
    if not playlists:
        utils.send_message(chat_id, f"No playlists found for {code}.")
    else:
        msg = f"🎥 Recommended Playlists for {code}:\n"
        for pl in playlists:
            msg += f"- {pl['title']}: {pl['link']}\n"
        utils.send_message(chat_id, msg)

# ---------- GPA / CGPA ----------
def handle_gpa(chat_id, args):
    """
    /gpa sgpa <SEM> GRADE1 GRADE2 ...
    /gpa cgpa <SEM1_SGPA> <SEM2_SGPA> ... (weighted by total credits in each semester)
    """

    if len(args) < 2:
        utils.send_message(chat_id, "Usage:\n/gpa sgpa <SEM> <grades...>\n/gpa cgpa <sgpa1> <sgpa2> ...")
        return

    mode = args[0].lower()

    if mode == "sgpa":
        try:
            sem = int(args[1])
            grades = args[2:]
        except Exception:
            utils.send_message(chat_id, "Usage: /gpa sgpa <SEM> <grades...>")
            return

        subjects = db.get_subjects_by_semester(sem)
        if not subjects:
            utils.send_message(chat_id, f"No subjects found for semester {sem}.")
            return

        if len(grades) != len(subjects):
            utils.send_message(chat_id, f"Provide {len(subjects)} grades (one per subject).")
            return

        total_points = 0
        total_credits = 0
        for subj, grade in zip(subjects, grades):
            gp = GRADE_POINTS.get(grade.upper())
            if gp is None:
                utils.send_message(chat_id, f"Invalid grade: {grade}")
                return
            c = subj.get("credits", 0)
            total_points += c * gp
            total_credits += c

        sgpa = total_points / total_credits if total_credits else 0
        utils.send_message(chat_id, f"📊 SGPA for Semester {sem} = {round(sgpa, 2)}")

    elif mode == "cgpa":
        # Weighted average of SGPA using total credits per semester
        try:
            sgpas = [float(x) for x in args[1:]]
        except ValueError:
            utils.send_message(chat_id, "CGPA values must be numbers.")
            return

        total_points = 0.0
        total_credits = 0
        for i, sgpa in enumerate(sgpas, start=1):
            subjects = db.get_subjects_by_semester(i)
            credits = sum(s.get("credits", 0) for s in subjects)
            total_points += sgpa * credits
            total_credits += credits

        cgpa = total_points / total_credits if total_credits else 0.0
        utils.send_message(chat_id, f"📊 CGPA up to Semester {len(sgpas)} = {round(cgpa, 2)}")

    else:
        utils.send_message(chat_id, "Unknown GPA mode. Use sgpa or cgpa.")

# ---------- File Helpers ----------
def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    resp = requests.get(url, timeout=60).json()
    return resp["result"]["file_path"]

def download_file(file_path):
    url = f"https://api.telegram.org/file/bot{config.TELEGRAM_TOKEN}/{file_path}"
    resp = requests.get(url, timeout=240)
    resp.raise_for_status()
    return resp.content
