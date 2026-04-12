import cv2
import time
import random
import threading

try:
    import mediapipe as mp
    mp_face = mp.solutions.face_mesh
    MEDIAPIPE_AVAILABLE = True
    print("[Pencil] MediaPipe loaded OK")
except (ImportError, AttributeError) as e:
    MEDIAPIPE_AVAILABLE = False
    print(f"[Pencil] MediaPipe tidak tersedia ({e}), jalan tanpa gaze detection")


def start_game(socketio, frame_holder):

    frame_holder["running"] = True
    print("[Pencil] Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[Pencil] ERROR: Webcam gagal dibuka!")
        frame_holder["running"] = False
        return 0

    print(f"[Pencil] Webcam OK: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

    face_mesh = None
    if MEDIAPIPE_AVAILABLE:
        face_mesh = mp_face.FaceMesh(refine_landmarks=True)

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

        if face_mesh is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(rgb)

            if result.multi_face_landmarks:
                lm = result.multi_face_landmarks[0].landmark
                pos_l = (lm[468].x - lm[33].x) / (lm[133].x - lm[33].x)
                pos_r = (lm[473].x - lm[362].x) / (lm[263].x - lm[362].x)

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

        cv2.putText(frame, f"Score: {score}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Draw pencil indicator
        pencil_x = w // 2
        pencil_y = h // 2
        cv2.circle(frame, (pencil_x, pencil_y), depth // 2, (0, 0, 255), 2)

        if not MEDIAPIPE_AVAILABLE:
            cv2.putText(frame, "MediaPipe not available - gaze detection OFF", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        with frame_holder["lock"]:
            frame_holder["frame"] = buffer.tobytes()

        time.sleep(0.03)

    cap.release()
    print(f"[Pencil] Game selesai. Frame: {frame_count}, Score: {score}")

    frame_holder["running"] = False
    return score
