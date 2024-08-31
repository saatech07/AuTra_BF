import os
import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from .forms import FileUploadForm
from .transcribe import transcribe_audio_file, is_supported_audio_file, is_audio_file, extract_audio_from_video
from .utils import cleanup_old_files
import mimetypes

class AudioFilePath:
    def __init__(self, base_name):
        self.base_name = base_name

class TextFilePath:
    def __init__(self, base_name):
        self.base_name = base_name

def transcribe_audio_view(request):
    cleanup_old_files()
    if request.method == 'POST':
        base_name = "default_name"
        form = FileUploadForm(request.POST, request.FILES)
        transcription = None
        text_file_path = None
        audio_file_path = None
        if form.is_valid():
            if 'file' in request.FILES:  # Handle uploaded file
                uploaded_file = request.FILES['file']
                base_name = os.path.splitext(os.path.basename(uploaded_file.name))[0]
                file_extension = os.path.splitext(uploaded_file.name)[1].lower().lstrip('.')
                if uploaded_file.name.endswith('mp4'):
                    temp_video_path = os.path.join(settings.MEDIA_ROOT, f"{base_name}.mp4")
                    with open(temp_video_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    extracted_audio_path = extract_audio_from_video(temp_video_path, base_name)
                    transcription = transcribe_audio_file(extracted_audio_path, base_name)

                elif is_supported_audio_file(file_extension) and is_audio_file(uploaded_file):
                    audio_file_path = os.path.join(settings.MEDIA_ROOT, f"audio/{base_name}.{file_extension}")
                    text_file_path = os.path.join(settings.MEDIA_ROOT, f"text/{base_name}.txt")

                    with open(audio_file_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    transcription = transcribe_audio_file(audio_file_path, base_name=base_name)
                else:
                    transcription = "Invalid file type. Please upload a supported audio file or a video (.mp4)."
                    text_file_path = None

            elif 'audio_link' in request.POST:  # Handle audio link
                audio_link = request.POST['audio_link']
                response = requests.get(audio_link, stream=True)

                if response.status_code == 200 and is_supported_audio_file(response.headers.get('content-type', '').split('/')[-1]):
                    base_name = os.path.basename(audio_link).split('.')[0]
                    audio_file_path = os.path.join(settings.MEDIA_ROOT, f"audio/{base_name}.wav")

                    with open(audio_file_path, 'wb+') as destination:
                        for chunk in response.iter_content(1024):
                            destination.write(chunk)

                    transcription = transcribe_audio_file(audio_file_path, base_name)

                else:
                    transcription = "Invalid audio link or unsupported format."
            if transcription:
                audio_file_path = AudioFilePath(base_name=base_name)
                text_file_path = TextFilePath(base_name=base_name)
                return render(request, 'transcribe/result.html', {
                    'audio_file_path': AudioFilePath(base_name=base_name) if audio_file_path else None,
                    'transcription': transcription,
                    'text_file_path': AudioFilePath(base_name=base_name) if text_file_path else None,
            })
    else:
        form = FileUploadForm()
    return render(request, 'transcribe/upload.html', {'form': form})


def download_audio(request, base_name):
    filename = f'audio/{base_name}.wav'
    media_root = settings.MEDIA_ROOT
    file_path = os.path.join(media_root, filename)
    try:
        with open(file_path, 'rb') as fl:
            mime_type, _ = mimetypes.guess_type(file_path)
            response = HttpResponse(fl, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % os.path.basename(filename)
            return response
    except FileNotFoundError:
        return HttpResponse("File not found.", status=404)

def download_text(request, base_name):
    filename = f'text/{base_name}.txt'
    media_root = settings.MEDIA_ROOT
    file_path = os.path.join(media_root, filename)
    try:
        with open(file_path, 'rb') as fl:
            mime_type, _ = mimetypes.guess_type(file_path)
            response = HttpResponse(fl, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % os.path.basename(filename)
            return response
    except FileNotFoundError:
        pass
    return HttpResponse("File not found.", status=404)


