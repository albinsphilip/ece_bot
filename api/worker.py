from flask import Flask, request, jsonify
import config
import db
import handlers
import utils
import json

app = Flask(__name__)

def _authorize(req) -> bool:
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {config.INTERNAL_API_TOKEN}"

@app.route("/api/worker", methods=["POST"])
def worker():
    if not _authorize(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    job_id = payload.get("job_id")
    if not job_id:
        return jsonify({"ok": False, "error": "job_id missing"}), 400

    job = db.get_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404

    if job.get("status") not in ("queued", "failed"):  # prevent reprocessing if already done
        return jsonify({"ok": True, "status": "skipped"})

    try:
        db.set_job_status(job_id, "processing")

        job_type = job["type"]
        chat_id = job["chat_id"]
        subject_code = job["subject_code"]

        if job_type == "pdf":
            # Download from Telegram & upload to Drive
            file_id = job["telegram_file_id"]
            file_path = handlers.get_file_path(file_id)
            file_bytes = handlers.download_file(file_path)
            drive_link = __upload_drive(file_bytes, job.get("original_filename", "note.pdf"))
            note_id = db.add_note(subject_code, drive_link, "pdf", chat_id,
                                  "approved" if config.AUTO_APPROVE else "pending")
            db.set_job_status(job_id, "done", {"note_id": note_id, "result_link": drive_link})
            utils.send_message(chat_id, f"✅ Upload successful for {subject_code}.\n📄 PDF link: {drive_link}\nNote ID: {note_id}")

        elif job_type == "youtube":
            link = job["link"]
            note_id = db.add_note(subject_code, link, "youtube", chat_id,
                                  "approved" if config.AUTO_APPROVE else "pending")
            db.set_job_status(job_id, "done", {"note_id": note_id})
            utils.send_message(chat_id, f"✅ Link saved for {subject_code}.\n🎥 {link}\nNote ID: {note_id}")

        else:
            db.set_job_status(job_id, "failed", {"error": "unknown job type"})
            utils.send_message(chat_id, "❌ Failed: unknown job type.")
            return jsonify({"ok": False, "error": "unknown job type"}), 400

        return jsonify({"ok": True, "status": "done"})

    except Exception as e:
        # Best-effort failure message
        try:
            db.set_job_status(job_id, "failed", {"error": str(e)})
            utils.send_message(job["chat_id"], f"❌ Upload failed for {job.get('subject_code', '')}: {e}")
        except Exception:
            pass
        return jsonify({"ok": False, "error": str(e)}), 500

def __upload_drive(file_bytes: bytes, filename: str):
    # Local import to avoid circular
    import drive_client
    return drive_client.upload_file(file_bytes, filename)
