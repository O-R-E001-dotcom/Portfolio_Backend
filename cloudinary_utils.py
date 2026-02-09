import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_project_image(file):
    result = cloudinary.uploader.upload(file, folder="portfolio/projects")
    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
    }


def delete_project_image(public_id: str):
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        # Best-effort cleanup
        pass