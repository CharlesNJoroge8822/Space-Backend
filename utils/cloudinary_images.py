import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv

#! Load environment variables from .env
load_dotenv()

#! Configure Cloudinary with your API keys
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(image_file, folder="profile_pictures"):
    """Uploads an image to Cloudinary and returns    the image URL."""
    try:
        response = cloudinary.uploader.upload(image_file, folder=folder)
        return response["secure_url"]  #! Return the image URL
    except Exception as e:
        return str(e)

def delete_image(public_id):
    """Deletes an image from Cloudinary."""
    try:
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        return str(e)
