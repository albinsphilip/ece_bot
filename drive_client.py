import requests
import config
from google.oauth2 import service_account
import google.auth.transport.requests

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def _get_access_token():
    creds = service_account.Credentials.from_service_account_info(
        config.GOOGLE_CREDS, scopes=SCOPES
    )
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

def upload_file(file_content: bytes, filename: str, mime_type: str = "application/pdf"):
    access_token = _get_access_token()
    metadata = {"name": filename}  # uploads to Service Account Drive root
    files = {
        "data": ("metadata", str(metadata), "application/json"),
        "file": (filename, file_content, mime_type),
    }
    response = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers={"Authorization": f"Bearer {access_token}"},
        files=files,
        timeout=240
    )
    response.raise_for_status()
    file_info = response.json()
    file_id = file_info["id"]

    # Make file public
    perm = requests.post(
        f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"role": "reader", "type": "anyone"},
        timeout=60
    )
    perm.raise_for_status()

    return f"https://drive.google.com/file/d/{file_id}/view"
