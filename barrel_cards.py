import cv2
import mediapipe as mp
import time
import random

# =============================
# INIT MEDIAPIPE
# =============================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# =============================
# GAME SETTINGS
# =============================
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

# =============================
# EYE LANDMARK INDEX
# =============================
LEFT_EYE_L = 33
LEFT_EYE_R = 133
LEFT_PUPIL = 468

RIGHT_EYE_L = 362
RIGHT_EYE_R = 263
RIGHT_PUPIL = 473

# =============================
# FUNCTIONS
# =============================
def get_eye_direction(lm):
    try:
        l_ratio = (lm[LEFT_PUPIL].x - lm[LEFT_EYE_L].x) / (lm[LEFT_EYE_R].x - lm[LEFT_EYE_L].x)
        r_ratio = (lm[RIGHT_PUPIL].x - lm[RIGHT_EYE_L].x) / (lm[RIGHT_EYE_R].x - lm[RIGHT_EYE_L].x)
        avg = (l_ratio + r_ratio) / 2

        if avg < 0.42:
            return "LEFT"
        elif avg > 0.58:
            return "RIGHT"
        else:
            return "CENTER"
    except:
        return None

def draw_barrels(frame, look_dir):
    for key, (x, y) in barrels.items():
        color = (255, 255, 255)
        if key == target:
            color = (255, 0, 255)   # TARGET
        if key == look_dir:
            color = (0, 255, 255)   # LOOKING

        cv2.rectangle(frame, (x, y), (x+BARREL_W, y+BARREL_H), color, 3)
        cv2.putText(frame, key, (x+20, y+90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

# =============================
# MAIN LOOP
# =============================
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

    # =============================
    # FOCUS LOGIC
    # =============================
    if look_dir == target:
        if focus_start is None:
            focus_start = time.time()
        elif time.time() - focus_start >= FOCUS_TIME:
            score += 10
            target = random.choice(list(barrels.keys()))
            focus_start = None
    else:
        focus_start = None

    draw_barrels(frame, look_dir)

    # =============================
    # UI TEXT
    # =============================
    cv2.putText(frame, f"TARGET: {target}", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

    cv2.putText(frame, f"SCORE: {score}", (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    if focus_start:
        progress = min((time.time() - focus_start) / FOCUS_TIME, 1.0)
        cv2.rectangle(frame, (30, 120), (30 + int(300 * progress), 140),
                      (0, 255, 0), -1)

    cv2.imshow("Barrel Cards Therapy - Eye Tracking", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
