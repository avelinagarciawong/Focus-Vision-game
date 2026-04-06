import cv2
import mediapipe as mp
import numpy as np


cap = cv2.VideoCapture(0)

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(refine_landmarks=True)

# Parameter pensil
depth = 40
min_depth = 40
max_depth = 140
speed = 1
direction = 1

FOCUS_MIN = 0.42
FOCUS_MAX = 0.58
def draw_pencil(img, center, size, color):
    x, y = center

    body_w = size // 4
    body_h = size

    # Badan pensil
    cv2.rectangle(
        img,
        (x - body_w // 2, y - body_h // 2),
        (x + body_w // 2, y + body_h // 2),
        color,
        -1
    )

    # Ujung pensil (segitiga)
    tip = np.array([
        [x - body_w // 2, y - body_h // 2],
        [x + body_w // 2, y - body_h // 2],
        [x, y - body_h // 2 - body_w]
    ])

    cv2.fillConvexPoly(img, tip, (60, 60, 60))

    # Penghapus
    cv2.rectangle(
        img,
        (x - body_w // 2, y + body_h // 2),
        (x + body_w // 2, y + body_h // 2 + body_w // 2),
        (200, 200, 200),
        -1
    )


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

        # Mata kiri
        eye_l_left = lm[33].x
        eye_l_right = lm[133].x
        iris_l = lm[468].x

        pos_l = (iris_l - eye_l_left) / (eye_l_right - eye_l_left)

        # Mata kanan
        eye_r_left = lm[362].x
        eye_r_right = lm[263].x
        iris_r = lm[473].x

        pos_r = (iris_r - eye_r_left) / (eye_r_right - eye_r_left)

        if (FOCUS_MIN < pos_l < FOCUS_MAX and
            FOCUS_MIN < pos_r < FOCUS_MAX):
            focused = True

    if focused:
        depth += speed * direction
        status = "FOCUS OK"
        color = (0, 255, 0)
    else:
        status = "LOOK AT THE PENCIL"
        color = (0, 0, 255)

    if depth >= max_depth:
        direction = -1
    elif depth <= min_depth:
        direction = 1

    draw_pencil(frame, (w // 2, h // 2), depth, color)

    cv2.putText(frame, status, (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("Pencil Push-Ups Therapy", frame)

    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()