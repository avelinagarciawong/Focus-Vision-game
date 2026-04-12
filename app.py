from flask import Flask, Response, send_from_directory
from flask_socketio import SocketIO
import threading
import time

import barrel_cards
import brodie_string_game
import pencil_pushup

app = Flask(__name__, static_folder="html", static_url_path="")
socketio = SocketIO(app, cors_allowed_origins="*")


# =========================
# PAGES
# =========================

@app.route("/")
def index():
    return send_from_directory("html", "home2.html")


@app.route("/html/<path:filename>")
def serve_html(filename):
    return send_from_directory("html", filename)

# =========================
# BRODIE FRAME HOLDER
# =========================

brodie_frame_holder = {"frame": None, "lock": threading.Lock(), "running": False}


def generate_brodie_frames():
    # Tunggu sampai game mulai (max 5 detik)
    for _ in range(100):
        if brodie_frame_holder["running"]:
            break
        time.sleep(0.05)
    while brodie_frame_holder["running"] or brodie_frame_holder["frame"] is not None:
        with brodie_frame_holder["lock"]:
            frame = brodie_frame_holder["frame"]
        if frame is not None:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        else:
            time.sleep(0.03)


@app.route("/video_feed/brodie")
def video_feed_brodie():
    return Response(generate_brodie_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# =========================
# PENCIL FRAME HOLDER
# =========================

pencil_frame_holder = {"frame": None, "lock": threading.Lock(), "running": False}


def generate_pencil_frames():
    for _ in range(100):
        if pencil_frame_holder["running"]:
            break
        time.sleep(0.05)
    while pencil_frame_holder["running"] or pencil_frame_holder["frame"] is not None:
        with pencil_frame_holder["lock"]:
            frame = pencil_frame_holder["frame"]
        if frame is not None:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        else:
            time.sleep(0.03)


@app.route("/video_feed/pencil")
def video_feed_pencil():
    return Response(generate_pencil_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# =========================
# EVENTS
# =========================

@socketio.on("start_barrel")
def start_barrel():
    thread = threading.Thread(target=run_barrel)
    thread.start()

def run_barrel():
    score = barrel_cards.start_game(socketio)
    socketio.emit("game_over", {"game": "barrel", "score": score})


@socketio.on("start_brodie")
def start_brodie():
    thread = threading.Thread(target=run_brodie)
    thread.start()

def run_brodie():
    try:
        brodie_frame_holder["running"] = True
        score = brodie_string_game.start_game(socketio, brodie_frame_holder)
        socketio.emit("game_over", {"game": "brodie", "score": score})
    except Exception as e:
        print(f"[Brodie] Error: {e}")
        socketio.emit("game_over", {"game": "brodie", "score": 0})
    finally:
        brodie_frame_holder["running"] = False


@socketio.on("start_pencil")
def start_pencil():
    thread = threading.Thread(target=run_pencil)
    thread.start()

def run_pencil():
    try:
        pencil_frame_holder["running"] = True
        score = pencil_pushup.start_game(socketio, pencil_frame_holder)
        socketio.emit("game_over", {"game": "pencil", "score": score})
    except Exception as e:
        print(f"[Pencil] Error: {e}")
        socketio.emit("game_over", {"game": "pencil", "score": 0})
    finally:
        pencil_frame_holder["running"] = False


if __name__ == "__main__":
    socketio.run(app, debug=True)