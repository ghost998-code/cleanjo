import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


async def upload_image(file_data: bytes, folder: str = "garbage_reports") -> str:
    import io
    from cloudinary.uploader import upload
    
    result = cloudinary.uploader.upload(
        file_data,
        folder=folder,
        resource_type="image",
    )
    return result["secure_url"]


async def delete_image(public_id: str) -> bool:
    result = cloudinary.uploader.destroy(public_id)
    return result.get("result") == "ok"
