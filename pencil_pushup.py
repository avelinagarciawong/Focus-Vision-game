import cv2
import mediapipe as mp
def start_game(socketio):

    cap = cv2.VideoCapture(0)
    mp_face = mp.solutions.face_mesh
    face_mesh = mp_face.FaceMesh(refine_landmarks=True)

    depth = 40
    min_depth = 40
    max_depth = 140
    speed = 1
    direction = 1

    score = 0

    FOCUS_MIN = 0.42    
    FOCUS_MAX = 0.58

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        focused = False

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

        cv2.imshow("Pencil Pushup", frame)

        if cv2.waitKey(30) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    return score