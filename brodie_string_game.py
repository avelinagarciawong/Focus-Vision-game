import cv2
import mediapipe as mp
import time
import random

# =========================
# SETUP KAMERA & MEDIAPIPE
# =========================
cap = cv2.VideoCapture(0)

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(refine_landmarks=True)

# =========================
# PARAMETER TERAPI
# =========================
HOLD_TIME = 2
CENTER_THRESHOLD = 0.009 # toleransi arah pandang

score = 0
focus_start = None

# =========================
# BEADS (DEPTH SIMULATION)
# =========================
beads = [
    {"y": 0.7, "size": 35},  # dekat
    {"y": 0.5, "size": 25},  # tengah
    {"y": 0.3, "size": 15},  # jauh
]

target = random.choice(beads)

# =========================
# GAME LOOP
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    focused = False

    # =========================
    # DETEKSI ARAH PANDANG MATA
    # =========================
    if result.multi_face_landmarks:
        lm = result.multi_face_landmarks[0].landmark

        left_iris = lm[468]
        right_iris = lm[473]

        gaze_x = (left_iris.x + right_iris.x) / 2
        gaze_y = (left_iris.y + right_iris.y) / 2

        # Fokus jika mata mengarah ke tengah layar
        if abs(gaze_x - 0.5) < CENTER_THRESHOLD:
            focused = True

    # =========================
    # LOGIKA TERAPI
    # =========================
    if focused:
        if focus_start is None:
            focus_start = time.time()
        elif time.time() - focus_start >= HOLD_TIME:
            score += 1
            target = random.choice(beads)
            focus_start = None
    else:
        focus_start = None

    # =========================
    # GAMBAR STRING (LURUS)
    # =========================
    cv2.line(
        frame,
        (w // 2, int(h * 0.2)),
        (w // 2, int(h * 0.8)),
        (200, 200, 200),
        3
    )

    # =========================
    # GAMBAR BEADS
    # =========================
    for b in beads:
        bx = w // 2
        by = int(b["y"] * h)

        if b == target:
            color = (0, 255, 0)  # target
        else:
            color = (0, 0, 255)

        cv2.circle(frame, (bx, by), b["size"], color, -1)

    # =========================
    # UI INFO
    # =========================
    status = "FOCUS OK" if focused else "LOOK STRAIGHT"
    status_color = (0, 255, 0) if focused else (0, 0, 255)

    cv2.putText(frame, status, (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

    cv2.putText(frame, f"Score: {score}", (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow("Brodie String Therapy Game", frame)

    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
