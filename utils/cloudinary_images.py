import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import logging
from dotenv import load_dotenv

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Ensure API credentials are loaded correctly
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    raise ValueError("❌ Cloudinary API credentials are missing! Check your .env file.")

# ✅ Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY, 
    api_secret=CLOUDINARY_API_SECRET
)

logging.info("✅ Cloudinary Config Loaded Successfully")

def upload_image(image_file, folder="profile_pictures"):
    """
    Uploads an image to Cloudinary and returns the image URL & public_id.
    """
    try:
        if not image_file:
            raise ValueError("❌ No image file provided.")

        # ✅ Log File Upload
        logging.info(f"🟢 Uploading {image_file.filename} to Cloudinary...")

        # ✅ Upload to Cloudinary
        response = cloudinary.uploader.upload(image_file, folder=folder)

        # ✅ Log & Return Success Response
        logging.info(f"✅ Upload Successful: {response['secure_url']}")
        return {
            "secure_url": response["secure_url"],
            "public_id": response["public_id"]
        }
    
    except Exception as e:
        logging.error(f"❌ Error Uploading Image: {e}")
        return {"error": str(e)}

def delete_image(public_id):
    """
    Deletes an image from Cloudinary and returns True/False.
    """
    try:
        if not public_id:
            raise ValueError("❌ No public_id provided for deletion.")

        # ✅ Log Deletion Attempt
        logging.info(f"🟢 Deleting image with public_id: {public_id}")

        # ✅ Perform Deletion
        response = cloudinary.uploader.destroy(public_id)

        # ✅ Log Deletion Success/Failure
        if response.get("result") == "ok":
            logging.info("✅ Image Deleted Successfully")
            return True
        else:
            logging.warning(f"⚠️ Image Deletion Failed: {response}")
            return False

    except Exception as e:
        logging.error(f"❌ Error Deleting Image: {e}")
        return False


# ✅ UPDATE USER IMAGE ROUTE
@user_bp.route("/users/<int:user_id>/update-image", methods=["PATCH"])
@jwt_required()
def update_image(user_id):
    """Update user profile image."""
    current_user_id = get_jwt_identity()  # Get authenticated user ID

    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized to update this profile"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["file"]
    
    try:
        # ✅ Upload the image to Cloudinary
        upload_result = upload_image(file)

        if "error" in upload_result:
            return jsonify({"error": upload_result["error"]}), 500

        # ✅ Update user image in database
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.image = upload_result["secure_url"]
        db.session.commit()

        return jsonify({
            "message": "Image updated successfully!",
            "image_url": user.image
        }), 200

    except Exception as e:
        db.session.rollback()  # Rollback any failed transactions
        return jsonify({"error": f"Failed to update image: {str(e)}"}), 500
