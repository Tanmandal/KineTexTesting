import requests
from io import BytesIO
from PIL import Image
import re
from datetime import datetime, timedelta, timezone


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


def getDateTime():
    # Define IST (UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))

    # Get current time in IST
    now_ist = datetime.now(IST)

    # Format without showing +05:30
    formatted_time = now_ist.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time
