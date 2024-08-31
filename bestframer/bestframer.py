import os
import cv2
import numpy as np
import mediapipe as mp
from django.conf import settings

mp_face_mesh = mp.solutions.face_mesh
mp_face_detection = mp.solutions.face_detection

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
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                return False

            landmarks = results.multi_face_landmarks[0].landmark

            left_eye_ratio = (landmarks[159].y - landmarks[145].y) / (landmarks[33].x - landmarks[133].x)
            right_eye_ratio = (landmarks[386].y - landmarks[374].y) / (landmarks[362].x - landmarks[263].x)

            mouth_ratio = landmarks[13].y - landmarks[14].y
            print(left_eye_ratio, right_eye_ratio, mouth_ratio)
            if left_eye_ratio > 0.09 and right_eye_ratio > 0.09 and mouth_ratio > 0:
                print("Good one")
                return True
            return False
    except (Exception,) as e:
        return None

def detect_and_crop_face(frame, padding=0.7):
    try:
        with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            if not hasattr(results, 'detections') or not results.detections:
                return None

            detection = results.detections[0]

            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape
            x, y, w, h = bboxC.xmin, bboxC.ymin, bboxC.width, bboxC.height

            # Apply padding
            pad_x = int(padding * w * iw)
            pad_y = int(padding * h * ih)

            crop_x1 = max(0, int(x * iw) - pad_x)
            crop_y1 = max(0, int(y * ih) - pad_y)
            crop_x2 = min(iw, int((x + w) * iw) + pad_x)
            crop_y2 = min(ih, int((y + h) * ih) + pad_y)

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
                print("Good frame")
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
