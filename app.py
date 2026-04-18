from flask import Flask, Response, send_from_directory, request, redirect, session, render_template
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
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
        database="web_focus_point"
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
    db = get_db()
    cursor = db.cursor(dictionary=True, buffered=True)

    email = session.get("user")

    if email:
        cursor.execute("SELECT username FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            return dict(username=user["username"])

    return dict(username="Guest")

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
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT user_id FROM users WHERE email=%s", (session["user"],))
    user = cursor.fetchone()

    cursor.execute("""
        SELECT game_name, MAX(score) as best_score
        FROM game_scores
        WHERE user_id=%s
        GROUP BY game_name
    """, (user["user_id"],))

    scores = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("dashboard.html", scores=scores)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    cursor = db.cursor(dictionary=True, buffered=True)

    email = session["user"]

    if request.method == "POST":
        new_username = request.form["username"].strip()

        # cek username duplicate
        cursor.execute("SELECT * FROM users WHERE username=%s", (new_username,))
        existing = cursor.fetchone()

        if existing and existing["email"] != email:
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            return render_template("profile.html", user=user, error="Username sudah digunakan!")

        cursor.execute("""
            UPDATE users 
            SET username=%s
            WHERE email=%s
        """, (new_username, email))

        db.commit()

        return redirect("/profile")

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    return render_template("profile.html", user=user)

@app.route("/games2")
@login_required
def games2():
    return render_template("games2.html")

@app.route("/save_score", methods=["POST"])
@login_required
def save_score():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    score = request.json["score"]
    game_name = request.json["game_name"]

    cursor.execute("SELECT user_id FROM users WHERE email=%s", (session["user"],))
    user = cursor.fetchone()

    if not user:
        return {"status": "error", "message": "User tidak ditemukan"}

    cursor.execute("""
        INSERT INTO game_scores (user_id, game_name, score)
        VALUES (%s, %s, %s)
    """, (user["user_id"], game_name, score))

    db.commit()

    return {"status": "success"}

@app.route("/home2")
@login_required
def home2():
    return render_template("home2.html")

@app.route("/notification")
@login_required
def notification():
    return render_template("notification.html")

@app.route("/privacy", methods=["GET", "POST"])
@login_required
def privacy():
    db = get_db()
    cursor = db.cursor(dictionary=True, buffered=True)

    email = session["user"]

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    # 🔥 CEGAH ERROR
    if not user:
        return render_template("privacy.html", error="User tidak ditemukan, silakan login ulang")

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(user["password"], current_password):
            return render_template("privacy.html", error="Password lama salah!")

        if new_password != confirm_password:
            return render_template("privacy.html", error="Password tidak sama!")

        hashed_password = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE users 
            SET password=%s
            WHERE email=%s
        """, (hashed_password, email))

        db.commit()

        return render_template("privacy.html", success="Password berhasil diubah!")

    return render_template("privacy.html")

@app.route("/about")
@login_required
def about():
    return render_template("about.html")

@app.route("/play_pencil_push_up")
@login_required
def play_pencil_push_up():
    return render_template("play_pencil_push_up.html")

from game_state import pencil_state, brodie_state

@socketio.on("pause_pencil")
def handle_pause(data):
    pencil_state["paused"] = data.get("paused", False)

@socketio.on("reset_pencil")
def handle_reset():
    pencil_state["reset"] = True
    pencil_frame_holder["running"] = False
    time.sleep(0.2)

@app.route("/start_game_pencil_push_up")
@login_required
def start_game_pencil_push_up():
    return render_template("start_game_pencil_push_up.html")

@app.route("/result_pencil_push_up")
@login_required
def result_pencil_push_up():
    return render_template("result_pencil_push_up.html")

@app.route("/play_bordie_strings")
@login_required
def play_bordie_strings():
    return render_template("play_bordie_strings.html")

@socketio.on("pause_brodie")
def handle_pause(data):
    brodie_state["paused"] = data.get("paused", False)

@socketio.on("reset_brodie")
def handle_reset():
    brodie_state["reset"] = True
    brodie_state["paused"] = False
    brodie_frame_holder["running"] = False
    time.sleep(0.2)
    brodie_state["reset"] = False

@app.route("/start_game_bordie_strings")
@login_required
def start_game_bordie_strings():
    return render_template("start_game_bordie_strings.html")

@app.route("/result_bordie_strings")
@login_required
def result_bordie_strings():
    return render_template("result_bordie_strings.html")

@app.route("/play_barrel_cards")
@login_required
def play_barrel_cards():
    return render_template("play_barrel_cards.html")

@app.route("/start_game_barrel_cards")
@login_required
def start_game_barrel_cards():
    return render_template("start_game_barrel_cards.html")

@app.route("/result_barrel_cards")
@login_required
def result_barrel_cards():
    return render_template("result_barrel_cards.html")

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
            session["user"] = user["email"]
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
def start_brodie(data=None):
    email = data.get("email") if data else None

    thread = threading.Thread(target=run_brodie, args=(email,))
    thread.start()

def run_brodie(email):
    try:
        brodie_frame_holder["running"] = True

        score = brodie_string_game.start_game(socketio, brodie_frame_holder)

        # 🔥 SIMPAN KE DATABASE
        if email:
            db = get_db()
            cursor = db.cursor(dictionary=True)

            cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user:
                cursor.execute("""
                    INSERT INTO game_scores (user_id, game_name, score)
                    VALUES (%s, %s, %s)
                """, (user["user_id"], "brodie_strings", score))

                db.commit()

            cursor.close()
            db.close()

        socketio.emit("game_over", {"game": "brodie", "score": score})

    except Exception as e:
        print(f"[Brodie] Error: {e}")
        socketio.emit("game_over", {"game": "brodie", "score": 0})

    finally:
        brodie_frame_holder["running"] = False


@socketio.on("start_pencil")
def start_pencil(data=None):
    if pencil_frame_holder["running"]:
        return  # 🔥 cegah double start

    email = data.get("email") if data else None

    thread = threading.Thread(target=run_pencil, args=(email,))
    thread.start()

def run_pencil(email):
    db = None
    cursor = None

    try:
        pencil_frame_holder["running"] = True
        score = pencil_pushup.start_game(socketio, pencil_frame_holder)

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            cursor.execute("""
                INSERT INTO game_scores (user_id, game_name, score)
                VALUES (%s, %s, %s)
            """, (user["user_id"], "pencil_push_up", score))
            db.commit()

        socketio.emit("game_over", {"game": "pencil", "score": score})

    except Exception as e:
        print(f"[Pencil] Error: {e}")
        socketio.emit("game_over", {"game": "pencil", "score": 0})

    finally:
        pencil_frame_holder["running"] = False

        if cursor:
            cursor.close()
        if db:
            db.close()


if __name__ == "__main__":
    socketio.run(app, debug=True)
