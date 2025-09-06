from flask import Flask, request, jsonify
import handlers
import utils

app = Flask(__name__)

@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    chat_id, text, document = utils.parse_update(update)
    if not chat_id:
        return jsonify({"ok": True})

    if text:
        parts = text.strip().split()
        cmd = parts[0].lower()

        if cmd == "/start":
            handlers.handle_start(chat_id)
        elif cmd == "/help":
            handlers.handle_help(chat_id)
        elif cmd == "/subject" and len(parts) > 1:
            handlers.handle_subject(chat_id, parts[1])
        elif cmd == "/upload" and len(parts) > 1:
            if len(parts) > 2:
                # Direct YouTube link in same message
                handlers.handle_upload(chat_id, parts[1], link=parts[2])
            else:
                handlers.handle_upload(chat_id, parts[1])
        elif cmd == "/pending":
            handlers.handle_pending(chat_id)
        elif cmd == "/approve" and len(parts) > 1:
            handlers.handle_approve(chat_id, parts[1])
        elif cmd == "/reject" and len(parts) > 1:
            handlers.handle_reject(chat_id, parts[1])
        else:
            if not handlers.handle_followup(chat_id, text=text):
                utils.send_message(chat_id, "Unknown command. Use /help.")
    elif document:
        if not handlers.handle_followup(chat_id, document=document):
            utils.send_message(chat_id, "❗ Please use /upload <CODE> before sending files.")

    return jsonify({"ok": True})
