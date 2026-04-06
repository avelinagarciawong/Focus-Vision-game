import cv2
import mediapipe as mp
import time
import random

def start_game(socketio):

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    cap = cv2.VideoCapture(0)

    BARREL_W = 120
    BARREL_H = 160
    Y_POS = 260

    barrels = {
        "LEFT":   (300, Y_POS),
        "CENTER": (580, Y_POS),
        "RIGHT":  (860, Y_POS)
    }

    FOCUS_TIME = 1.5
    focus_start = None
    score = 0
    target = random.choice(list(barrels.keys()))

    def get_eye_direction(lm):
        try:
            l_ratio = (lm[468].x - lm[33].x) / (lm[133].x - lm[33].x)
            r_ratio = (lm[473].x - lm[362].x) / (lm[263].x - lm[362].x)
            avg = (l_ratio + r_ratio) / 2

            if avg < 0.42:
                return "LEFT"
            elif avg > 0.58:
                return "RIGHT"
            else:
                return "CENTER"
        except:
            return None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        look_dir = None

        if result.multi_face_landmarks:
            lm = result.multi_face_landmarks[0].landmark
            look_dir = get_eye_direction(lm)

        if look_dir == target:
            if focus_start is None:
                focus_start = time.time()
            elif time.time() - focus_start >= FOCUS_TIME:
                score += 10
                target = random.choice(list(barrels.keys()))
                focus_start = None

                socketio.emit("score_update", {"game": "barrel", "score": score})

        else:
            focus_start = None

        cv2.putText(frame, f"SCORE: {score}", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Barrel Cards", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    return score