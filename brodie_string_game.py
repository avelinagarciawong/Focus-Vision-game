import cv2
import time
import random
import threading

try:
    import mediapipe as mp
    mp_face = mp.solutions.face_mesh
    MEDIAPIPE_AVAILABLE = True
    print("[Brodie] MediaPipe loaded OK")
except (ImportError, AttributeError) as e:
    MEDIAPIPE_AVAILABLE = False
    print(f"[Brodie] MediaPipe tidak tersedia ({e}), jalan tanpa gaze detection")


def start_game(socketio, frame_holder):

    frame_holder["running"] = True
    print("[Brodie] Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[Brodie] ERROR: Webcam gagal dibuka!")
        frame_holder["running"] = False
        return 0

    print(f"[Brodie] Webcam OK: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

    face_mesh = None
    if MEDIAPIPE_AVAILABLE:
        face_mesh = mp_face.FaceMesh(refine_landmarks=True)

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

        if face_mesh is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(rgb)

            if result.multi_face_landmarks:
                lm = result.multi_face_landmarks[0].landmark
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

        cv2.putText(frame, f"Score: {score}", (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        bead_x = w // 2
        bead_y = int(target["y"] * h)
        cv2.circle(frame, (bead_x, bead_y), target["size"], (0, 255, 0), 2)

        if not MEDIAPIPE_AVAILABLE:
            cv2.putText(frame, "MediaPipe not available - gaze detection OFF", (30, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        with frame_holder["lock"]:
            frame_holder["frame"] = buffer.tobytes()

        time.sleep(0.03)

    cap.release()
    print(f"[Brodie] Game selesai. Frame: {frame_count}, Score: {score}")

    frame_holder["running"] = False
    return score
