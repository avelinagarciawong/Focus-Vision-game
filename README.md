# Focus Point - Eye Therapy Vision Training

Aplikasi web untuk terapi penglihatan menggunakan webcam dan deteksi gaze berbasis MediaPipe. Terdiri dari 3 game:

- **Pencil Push-Up** — Latihan koordinasi mata dengan mengikuti objek bergerak
- **Brodie String (Brock String)** — Latihan fokus mata pada bead di posisi berbeda
- **Barrel Cards** — Latihan kemampuan fokus mata

## Prasyarat

- Python 3.8+
- Webcam
- Browser modern (Chrome, Firefox, Safari, Edge)

## Instalasi

```bash
# Clone / masuk ke folder project
cd focuspoint

# (Opsional) Buat virtual environment
python -m venv venv
source venv/bin/activate

# Install dependensi
pip install -r requirements.txt
```

### Catatan MediaPipe

Jika MediaPipe gagal load (error `module 'mediapipe' has no attribute 'solutions'`), coba:

```bash
pip uninstall mediapipe -y
pip install mediapipe==0.10.11
```

Game tetap bisa jalan tanpa MediaPipe (webcam stream aktif, tapi gaze detection nonaktif).

## Menjalankan

```bash
python app.py
```

Server berjalan di `http://127.0.0.1:5000`.

## Halaman

| URL | Deskripsi |
|-----|-----------|
| `/` | Homepage |
| `/play_bordie_strings.html` | Game Brodie String |
| `/play_pencil_push_up.html` | Game Pencil Push-Up |
| `/start_game_barrel_cards.html` | Game Barrel Cards |

## Arsitektur

```
Browser ──SocketIO──▶ Flask Server ──Thread──▶ Game Engine
   ▲                      │                        │
   │                      │                   cv2.VideoCapture
   │◀── MJPEG Stream ◀───┘                        │
   │    /video_feed/*                         Frame JPEG
   │                                               │
   │◀── SocketIO events ◀────────────────── score_update
        (score_update, game_over)             game_over
```

- Webcam frame di-stream ke browser via MJPEG over HTTP
- Skor dan event game dikirim via SocketIO
- Setiap game punya endpoint stream sendiri (`/video_feed/brodie`, `/video_feed/pencil`)

## Struktur File

```
├── app.py                  # Flask server utama
├── brodie_string_game.py   # Game engine Brodie String
├── pencil_pushup.py        # Game engine Pencil Push-Up
├── barrel_cards.py         # Game engine Barrel Cards
├── requirements.txt        # Dependensi Python
├── html/                   # File HTML, CSS, dan aset
│   ├── home2.html          # Homepage
│   ├── play_bordie_strings.html
│   ├── play_pencil_push_up.html
│   ├── css/                # Stylesheet
│   └── icon/               # Ikon dan gambar
└── tests/                  # Unit & integration test
```

## Menjalankan Test

```bash
pip install pytest numpy
pytest tests/ -v
```
