import cv2
import time
import random
import threading
import os

MEDIAPIPE_AVAILABLE = False
landmarker = None

try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions

    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task")
    if os.path.exists(model_path):
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1
        )
        landmarker = vision.FaceLandmarker.create_from_options(options)
        MEDIAPIPE_AVAILABLE = True
        print("[Pencil] FaceLandmarker loaded OK")
    else:
        print(f"[Pencil] Model not found: {model_path}")
except Exception as e:
    print(f"[Pencil] MediaPipe error: {e}")


def start_game(socketio, frame_holder):

    frame_holder["running"] = True
    print("[Pencil] Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[Pencil] ERROR: Webcam gagal dibuka!")
        frame_holder["running"] = False
        return 0

    w_cam = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_cam = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Pencil] Webcam OK: {w_cam}x{h_cam}")

    # Countdown 3, 2, 1
    for count in [3, 2, 1]:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            text = str(count)
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 4
            thickness = 8
            (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
            cx = (w - tw) // 2
            cy = (h + th) // 2
            cv2.putText(frame, text, (cx, cy), font, scale, (0, 255, 255), thickness)
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            with frame_holder["lock"]:
                frame_holder["frame"] = buffer.tobytes()
        time.sleep(1)

    depth = 40
    min_depth = 40
    max_depth = 140
    speed = 1
    direction = 1

    score = 0
    FOCUS_MIN = 0.42
    FOCUS_MAX = 0.58

    print("[Pencil] Game loop dimulai...")
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"[Pencil] cap.read() gagal setelah {frame_count} frame")
            break

        frame_count += 1
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        focused = False

        if MEDIAPIPE_AVAILABLE and landmarker is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect(mp_image)

            if result.face_landmarks:
                lm = result.face_landmarks[0]
                pos_l = (lm[468].x - lm[33].x) / (lm[133].x - lm[33].x + 1e-6)
                pos_r = (lm[473].x - lm[362].x) / (lm[263].x - lm[362].x + 1e-6)
                if FOCUS_MIN < pos_l < FOCUS_MAX and FOCUS_MIN < pos_r < FOCUS_MAX:
                    focused = True

        if focused:
            depth += speed * direction
            score += 1
            socketio.emit("score_update", {"game": "pencil", "score": score})

        if depth >= max_depth:
            direction = -1
        elif depth <= min_depth:
            direction = 1

        pencil_x = w // 2
        pencil_y = h // 2
        cv2.circle(frame, (pencil_x, pencil_y), depth // 2, (0, 0, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        with frame_holder["lock"]:
            frame_holder["frame"] = buffer.tobytes()

        time.sleep(0.03)

    cap.release()
    print(f"[Pencil] Game selesai. Frame: {frame_count}, Score: {score}")

    frame_holder["running"] = False
    return score
