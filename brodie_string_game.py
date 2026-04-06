import cv2
import mediapipe as mp
import time
import random

def start_game(socketio):

    cap = cv2.VideoCapture(0)
    mp_face = mp.solutions.face_mesh
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

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        focused = False

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

        cv2.imshow("Brodie String", frame)

        if cv2.waitKey(30) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    return score