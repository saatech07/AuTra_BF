from django.core.files.uploadedfile import UploadedFile
from django.http import FileResponse, HttpResponse
import logging
from datetime import datetime, timedelta
from django.shortcuts import render
import os
import cv2
from .bestframer import get_best_frame_from_web, get_best_frame_from_video
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_filename(base_dir, base_name):
    base_name = os.path.basename(base_name)
    filename = f"my_bestframe/{base_name}.jpeg"
    file_path = os.path.join(base_dir, filename)
    return file_path, base_name


def process_video(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        video_file = request.FILES.get('video_file')
        if video_url:
            filename, cropped_frame = get_best_frame_from_web(video_url)
            if filename and cropped_frame is not None:
                file_path, base_filename = generate_filename(settings.MEDIA_ROOT, filename)
                try:
                    cv2.imwrite(file_path, cropped_frame)
                    return render(request, 'best_framer/best_frame.html',
                                  {'best_frame': base_filename, 'video_url': video_url})
                except Exception as e:
                    logger.error(f"Error saving image: {e}")
                    return HttpResponse("Error saving best frame.")
            else:
                return HttpResponse("No face detected in the best frame from web video.")

        elif video_file:
            if isinstance(video_file, UploadedFile):
                base_filename, _ = os.path.splitext(video_file.name)
                temp_path = os.path.join(settings.MEDIA_ROOT, f"my_bestframe/videos/{video_file.name}")
                with open(temp_path, 'wb+') as destination:
                    for chunk in video_file.chunks():
                        destination.write(chunk)
                cap = cv2.VideoCapture(temp_path)
                if not cap.isOpened():
                    return HttpResponse("Failed to open the video file.")
                filename, cropped_frame = get_best_frame_from_video(cap, video_file)
                cap.release()
                os.remove(temp_path)
                if filename and cropped_frame is not None:
                    file_path, base_filename = generate_filename(settings.MEDIA_ROOT, base_filename)
                    try:
                        cv2.imwrite(file_path, cropped_frame)
                        return render(request, 'best_framer/best_frame.html',
                                      {'best_frame': base_filename, 'video_file': video_file})
                    except Exception as e:
                        logger.error(f"Error saving image: {e}")
                        return HttpResponse("Error saving best frame.")
                else:
                    return HttpResponse("No face detected in the best frame from the video file.")
            else:
                return HttpResponse("Invalid video file uploaded.")
        else:
            return HttpResponse("Please enter a valid video URL or select a video file.")
    else:
        return render(request, 'best_framer/index.html')
def download_image(request, filename):
    filename = os.path.basename(filename)
    file_path = os.path.join(settings.MEDIA_ROOT, f"my_bestframe/{filename}.jpeg")
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f"{filename}.jpeg")
    else:
        return HttpResponse("File not found.")
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