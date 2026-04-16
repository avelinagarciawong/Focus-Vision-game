from flask import Flask, Response, send_from_directory, request, redirect, session, render_template
import mysql.connector
from werkzeug.security import check_password_hash
from flask_socketio import SocketIO
from functools import wraps
import threading
import time

import barrel_cards
import brodie_string_game
import pencil_pushup

app = Flask(__name__, template_folder="html", static_folder="html", static_url_path="")
app.secret_key = "secret123"
socketio = SocketIO(app, cors_allowed_origins="*")

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="focus_point"
    )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# =========================
# PAGES
# =========================

@app.context_processor
def inject_user():
    return dict(username=session.get("user", "Guest"))

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/")
def index():
    if "user" in session:
        return render_template("home2.html")
    else:
        return redirect("/login")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    old_username = session["user"]

    if request.method == "POST":
        new_username = request.form["username"].strip()

        # 🔥 VALIDASI USERNAME
        cursor.execute("SELECT * FROM users WHERE username=%s", (new_username,))
        existing = cursor.fetchone()

        if existing and existing["username"] != old_username:
            cursor.execute("SELECT * FROM users WHERE username=%s", (old_username,))
            user = cursor.fetchone()
            return render_template("profile.html", user=user, error="Username sudah digunakan!")

        try:
            cursor.execute("""
                UPDATE users 
                SET username=%s
                WHERE username=%s
            """, (new_username, old_username))

            db.commit()

            # update session
            session["user"] = new_username

            cursor.execute("SELECT * FROM users WHERE username=%s", (new_username,))
            user = cursor.fetchone()

            return render_template("profile.html", user=user, success="Username berhasil diupdate!")

        except mysql.connector.Error as e:
            print("MYSQL ERROR:", e)
            cursor.execute("SELECT * FROM users WHERE username=%s", (old_username,))
            user = cursor.fetchone()
            return render_template("profile.html", user=user, error="Terjadi error saat update!")

    # GET
    cursor.execute("SELECT * FROM users WHERE username=%s", (old_username,))
    user = cursor.fetchone()

    return render_template("profile.html", user=user)

@app.route("/games2")
@login_required
def games2():
    return render_template("games2.html")

@app.route("/home2")
@login_required
def home2():
    return render_template("home2.html")

@app.route("/notification")
@login_required
def notification():
    return render_template("notification.html")

@app.route("/privacy")
@login_required
def privacy():
    return render_template("privacy.html")

@app.route("/about")
@login_required
def about():
    return render_template("about.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# =========================
# PROSES LOGIN
# =========================

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user:
        if check_password_hash(user["password"], password):
            session["user"] = user["username"]
            return redirect("/")  # ke home2.html
        else:
            return "Password salah!"
    else:
        return "Email tidak ditemukan!"

@app.route("/session")
def get_session():
    return {"user": session.get("user")}

# =========================
# PROSES REGISTER
# =========================

from werkzeug.security import generate_password_hash

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
        (username, email, password),
    )

    db.commit()

    return redirect("/login")

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