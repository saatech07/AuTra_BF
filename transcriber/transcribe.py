from moviepy.editor import VideoFileClip
from django.conf import settings
import mimetypes
import whisper
import os
import logging

SUPPORTED_AUDIO_FORMATS = {'wav', 'mp3', 'flac', 'aac', 'ogg'}

logger = logging.getLogger(__name__)

def is_supported_audio_file(file_extension):
    return file_extension.lower() in SUPPORTED_AUDIO_FORMATS

def is_audio_file(file):
    mime_type, _ = mimetypes.guess_type(file.name)
    return mime_type and mime_type.startswith('audio')


def save_text_to_file(transcription_text, base_name):
    text_file_path = os.path.join(settings.MEDIA_ROOT, f"text/{base_name}.txt")
    os.makedirs(os.path.dirname(text_file_path), exist_ok=True)

    try:
        with open(text_file_path, 'w') as file:
            file.write(transcription_text)
        logger.info(f"Transcription saved to: {text_file_path}")
        return text_file_path
    except IOError as e:
        logger.error(f"Error saving transcription to file: {e}")
        return None


def transcribe_audio_file(audio_file_path, base_name):
    logger.info(f"Transcribing audio: {audio_file_path}")
    try:
        model = whisper.load_model("medium")
        result = model.transcribe(audio_file_path)
        transcription_text = result['text']

        transcription_file_path = save_text_to_file(transcription_text, base_name)
        return transcription_text, transcription_file_path
    except whisper.DecodingError as e:
        logger.error(f"Decoding error during transcription: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return None, None

def extract_audio_from_video(video_file_path, base_name):
    audio_file_path = os.path.join(settings.MEDIA_ROOT, f"audio/{base_name}.wav")
    logger.info(f"Saving audio file to: {audio_file_path}")

    try:
        video = VideoFileClip(video_file_path)
        audio = video.audio
        audio.write_audiofile(audio_file_path)

        audio.close()
        video.close()

        logger.info(f"Audio file saved at: {audio_file_path}")
        return audio_file_path

    except (IOError, OSError) as e:
        logger.error(f"Error extracting audio: {e}")
        return None
