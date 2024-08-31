import os
import cv2
import numpy as np
import dlib
from django.conf import settings

detector = dlib.get_frontal_face_detector()
shaper_file = "shape_predictor_68_face_landmarks.dat"
dependency = os.path.join(settings.MEDIA_ROOT, f"dependencies/{shaper_file}")
predictor = dlib.shape_predictor(dependency)

def calculate_brightness(frame):
    try:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        brightness = np.mean(hsv[:, :, 2])
        return brightness
    except (Exception,) as e:
        return None

def calculate_contrast(frame):
    try:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        contrast = gray_frame.std()
        return contrast
    except (Exception,) as e:
        return None

def calculate_sharpness(frame):
    try:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray_frame, cv2.CV_64F).var()
        return sharpness
    except (Exception,) as e:
        return None

def extract_filename_from_url(url):
    try:
        basename = os.path.basename(url)
        filename, _ = os.path.splitext(basename)
        return filename
    except (Exception,) as e:
        return None

def is_good_frame(frame):
    try:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray_frame)

        if len(faces) == 0:
            return False
        face = faces[0]
        landmarks = predictor(gray_frame, face)

        left_eye_ratio = (landmarks.part(44).y - landmarks.part(48).y) / (landmarks.part(43).x - landmarks.part(46).x)
        right_eye_ratio = (landmarks.part(39).y - landmarks.part(41).y) / (landmarks.part(37).x - landmarks.part(40).x)
        mouth_ratio =  (landmarks.part(62).y + landmarks.part(68).y) - (landmarks.part(63).y - landmarks.part(67).y) + (landmarks.part(64).y - landmarks.part(66).y) / (landmarks.part(61).x - landmarks.part(65).x)
        print(left_eye_ratio,right_eye_ratio,mouth_ratio)
        if left_eye_ratio > 0.06 and right_eye_ratio > 0.06 and mouth_ratio > 2.2:
            print("Good one")
            return True
        return False
    except (Exception,) as e:
        return None

def detect_and_crop_face(frame, padding=0.7):
    try:
        cascade_file = os.path.join(settings.MEDIA_ROOT, 'cascades/haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(cascade_file)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if face_cascade.empty():
            return None

        if len(faces) == 0:
            return None

        (x, y, w, h) = faces[0]

        pad_x = int(padding * w)
        pad_y = int(padding * h)

        crop_x1 = max(0, x - pad_x)
        crop_y1 = max(0, y - pad_y)
        crop_x2 = min(frame.shape[1], x + w + pad_x)
        crop_y2 = min(frame.shape[0], y + h + pad_y)

        cropped_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        return cropped_frame
    except (Exception,) as e:
        return None

def get_best_frame_from_web(video_url):
    try:
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            return None, None

        return get_best_frame_from_video(cap, extract_filename_from_url(video_url))
    except (Exception,) as e:
        return None, None

def get_best_frame_from_video(cap, filename):
    best_frame = None
    best_score = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames_to_skip = int(fps/4)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frames_to_skip == 0:
            if is_good_frame(frame):
                print("Good fda")
                sharpness = calculate_sharpness(frame)
                brightness = calculate_brightness(frame)
                contrast = calculate_contrast(frame)

                if sharpness is not None and contrast is not None and brightness is not None:
                    score = (0.6 * sharpness) + (0.3 * contrast) + (0.2 * brightness)
                    if score > best_score:
                        best_score = score
                        best_frame = frame

        frame_count += 1

    cap.release()

    if best_frame is not None:
        cropped_frame = detect_and_crop_face(best_frame)
        if cropped_frame is not None:
            return filename, cropped_frame
        else:
            return filename, best_frame
    return filename, None

def get_best_frame(video_input):
    if video_input.startswith("http"):
        return get_best_frame_from_web(video_input)
    else:
        cap = cv2.VideoCapture(video_input)
        if not cap.isOpened():
            return None, None
        return get_best_frame_from_video(cap, os.path.splitext(os.path.basename(video_input))[0])
