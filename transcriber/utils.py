import os
from datetime import datetime, timedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def cleanup_old_files():
    now = datetime.now()
    cutoff = now - timedelta(days=3)
    media_path = settings.MEDIA_ROOT
    for filename in os.listdir(media_path):
        file_path = os.path.join(media_path, filename)
        try:
            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < cutoff:
                    os.remove(file_path)
                    logger.info(f"Deleted old file: {filename}")
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
