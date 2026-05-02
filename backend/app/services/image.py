from datetime import datetime
from pathlib import Path
import uuid

from app.core.config import settings


def build_report_folder() -> str:
    now = datetime.utcnow()
    return f"reports/{now.year}/{now.month:02d}"


def build_local_upload_path(resource_type: str, folder: str | None = None) -> tuple[Path, str]:
    target_folder = Path(settings.LOCAL_UPLOAD_DIR) / (folder or build_report_folder())
    target_folder.mkdir(parents=True, exist_ok=True)

    if resource_type == "image":
        suffix = ".jpg"
    elif resource_type == "video":
        suffix = ".mp4"
    else:
        suffix = ".bin"

    file_name = f"{uuid.uuid4().hex}{suffix}"
    file_path = target_folder / file_name
    relative_path = file_path.relative_to(Path(settings.LOCAL_UPLOAD_DIR)).as_posix()
    return file_path, f"{settings.PUBLIC_BASE_URL.rstrip('/')}/uploads/{relative_path}"


async def upload_media(
    file_data: bytes,
    *,
    resource_type: str,
    folder: str | None = None,
) -> str:
    file_path, public_url = build_local_upload_path(resource_type, folder)
    file_path.write_bytes(file_data)
    return public_url


async def upload_image(file_data: bytes, folder: str | None = None) -> str:
    return await upload_media(file_data, resource_type="image", folder=folder)


async def upload_video(file_data: bytes, folder: str | None = None) -> str:
    return await upload_media(file_data, resource_type="video", folder=folder)


async def delete_image(public_id: str) -> bool:
    if not public_id.startswith(f"{settings.PUBLIC_BASE_URL.rstrip('/')}/uploads/"):
        return False

    relative_path = public_id.split("/uploads/", 1)[1]
    file_path = Path(settings.LOCAL_UPLOAD_DIR) / relative_path
    if file_path.exists():
        file_path.unlink()
        return True
    return False
