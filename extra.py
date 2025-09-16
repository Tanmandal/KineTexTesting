import requests
from io import BytesIO
from PIL import Image
import re
from datetime import datetime, timedelta, timezone
import os
import mimetypes
import base64
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions


def gdriveimg(url):
    """
    Returns a PIL Image from any URL.
    If the URL is a Google Drive link, it auto-converts to a direct link.
    """
    # Check if Google Drive link
    if "drive.google.com" in url:
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if match:
            file_id = match.group(1)
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
        else:
            return "https://upload.wikimedia.org/wikipedia/commons/a/a6/Pictogram_voting_comment.svg"  # invalid gdrive link

    # Fetch image from URL
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error loading image: {e}")
        return "https://upload.wikimedia.org/wikipedia/commons/a/a6/Pictogram_voting_comment.svg"


"""
def gimageconvert(url: str) -> str:
    if "drive.google.com" not in url:
        return url  # not a Google Drive link

    file_id = None

    # Match the /d/<id>/ format
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        file_id = match.group(1)

    # Match the id=<id> format
    if not file_id:
        match = re.search(r"id=([a-zA-Z0-9_-]+)", url)
        if match:
            file_id = match.group(1)

    if file_id:
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"#f"https://lh3.googleusercontent.com/d/{file_id}=w600-h600"
    else:
        return url  # fallback if no match
"""

def getDateTime():
    # Define IST (UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))

    # Get current time in IST
    now_ist = datetime.now(IST)

    # Format without showing +05:30
    formatted_time = now_ist.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time



def gimageconvert(url: str, file_name: str = None, folder: str = "/uploads/") -> str:
    """
    Fetch an image (Google Drive or any URL), convert to base64,
    and upload to ImageKit. Returns ImageKit URL on success.
    """
    imagekit = ImageKit(
        private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
        public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
        url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT")
    )
    try:
        # --- Step 1: Handle Google Drive links ---
        file_id = None
        if "drive.google.com" in url:
            match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
            if match:
                file_id = match.group(1)
            else:
                match = re.search(r"id=([a-zA-Z0-9_-]+)", url)
                if match:
                    file_id = match.group(1)

            if file_id:
                url = f"https://drive.google.com/uc?export=download&id={file_id}"

        # --- Step 2: Fetch image ---
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").split(";")[0]
        if not content_type.startswith("image/"):
            #print("❌ Not an image, got:", content_type)
            return url

        ext = mimetypes.guess_extension(content_type) or ".jpg"
        filename = file_name or f"fetched_{file_id or 'image'}{ext}"

        # --- Step 3: Convert to Base64 ---
        file_b64 = base64.b64encode(response.content).decode("utf-8")
        file_data = f"data:{content_type};base64,{file_b64}"

        # --- Step 4: Upload to ImageKit ---
        options = UploadFileRequestOptions(
            folder=folder,
            use_unique_file_name=False,
            tags=['auto-upload'],
            is_private_file=False,
            overwrite_file=True
        )

        result = imagekit.upload_file(
            file=file_data,          # ✅ base64 string
            file_name=filename,
            options=options
        )

        #print("✅ Upload complete:", result.url)
        return result.url

    except Exception as e:
        #print("❌ Error in gimageconvert:", e)
        return url
