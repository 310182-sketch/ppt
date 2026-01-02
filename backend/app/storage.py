import os
from typing import Optional


def upload_local_file(src_path: str, job_id: str, filename: Optional[str] = None) -> str:
    """
    Simple local "upload" for dev: copy file into storage/<job_id>/
    Returns destination path.
    """
    base = os.environ.get("BACKEND_STORAGE_PATH", "/workspaces/ppt/backend/storage")
    dest_dir = os.path.join(base, job_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest_name = filename if filename else os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, dest_name)
    with open(src_path, "rb") as fr, open(dest_path, "wb") as fw:
        fw.write(fr.read())
    return dest_path


def make_signed_url(dest_path: str) -> str:
    """
    Dev helper: return a file:// path or absolute path that client can use.
    In production, generate real signed URL from GCS/S3.
    """
    return "file://" + os.path.abspath(dest_path)
