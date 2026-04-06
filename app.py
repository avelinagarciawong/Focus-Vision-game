from flask import Flask
from flask_socketio import SocketIO
import threading

import barrel_cards
import brodie_string_game
import pencil_pushup

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    score = brodie_string_game.start_game(socketio)
    socketio.emit("game_over", {"game": "brodie", "score": score})


@socketio.on("start_pencil")
def start_pencil():
    thread = threading.Thread(target=run_pencil)
    thread.start()

def run_pencil():
    score = pencil_pushup.start_game(socketio)
    socketio.emit("game_over", {"game": "pencil", "score": score})


if __name__ == "__main__":
    socketio.run(app, debug=True)