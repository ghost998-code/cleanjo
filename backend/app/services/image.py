from datetime import datetime

import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


def build_report_folder() -> str:
    now = datetime.utcnow()
    return f"reports/{now.year}/{now.month:02d}"


async def upload_media(
    file_data: bytes,
    *,
    resource_type: str,
    folder: str | None = None,
) -> str:
    result = cloudinary.uploader.upload(
        file_data,
        folder=folder or build_report_folder(),
        resource_type=resource_type,
    )
    return result["secure_url"]


async def upload_image(file_data: bytes, folder: str | None = None) -> str:
    return await upload_media(file_data, resource_type="image", folder=folder)


async def upload_video(file_data: bytes, folder: str | None = None) -> str:
    return await upload_media(file_data, resource_type="video", folder=folder)


async def delete_image(public_id: str) -> bool:
    result = cloudinary.uploader.destroy(public_id)
    return result.get("result") == "ok"
