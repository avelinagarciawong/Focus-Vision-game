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
        print("[Brodie] FaceLandmarker loaded OK")
    else:
        print(f"[Brodie] Model not found: {model_path}")
except Exception as e:
    print(f"[Brodie] MediaPipe error: {e}")


def start_game(socketio, frame_holder):

    frame_holder["running"] = True
    print("[Brodie] Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[Brodie] ERROR: Webcam gagal dibuka!")
        frame_holder["running"] = False
        return 0

    w_cam = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_cam = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Brodie] Webcam OK: {w_cam}x{h_cam}")

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

    HOLD_TIME = 2
    CENTER_THRESHOLD = 0.009

    score = 0
    focus_start = None

    beads = [
        {"y": 0.7, "size": 35},
        {"y": 0.5, "size": 25},
        {"y": 0.3, "size": 15},
    ]

    target = random.choice(beads)
    print("[Brodie] Game loop dimulai...")
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"[Brodie] cap.read() gagal setelah {frame_count} frame")
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
                # Iris landmarks: 468-472 (left), 473-477 (right)
                gaze_x = (lm[468].x + lm[473].x) / 2
                if abs(gaze_x - 0.5) < CENTER_THRESHOLD:
                    focused = True

        if focused:
            if focus_start is None:
                focus_start = time.time()
            elif time.time() - focus_start >= HOLD_TIME:
                score += 1
                target = random.choice(beads)
                focus_start = None
                socketio.emit("score_update", {"game": "brodie", "score": score})
        else:
            focus_start = None

        bead_x = w // 2
        bead_y = int(target["y"] * h)
        cv2.circle(frame, (bead_x, bead_y), target["size"], (0, 255, 0), 2)

        if not MEDIAPIPE_AVAILABLE:
            cv2.putText(frame, "MediaPipe not available", (30, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        with frame_holder["lock"]:
            frame_holder["frame"] = buffer.tobytes()

        time.sleep(0.03)

    cap.release()
    print(f"[Brodie] Game selesai. Frame: {frame_count}, Score: {score}")

    frame_holder["running"] = False
    return score
