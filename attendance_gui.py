import cv2
import mediapipe as mp
import numpy as np
import os
import sqlite3
import csv
from datetime import datetime
from numpy.linalg import norm
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from skimage.feature import local_binary_pattern, hog

# ======================================================
# DATABASE
# ======================================================
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    class_name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    student_id TEXT,
    date TEXT,
    time TEXT
)
""")
conn.commit()

# ======================================================
# FEATURE EXTRACTION
# ======================================================
def extract_features(face_img):
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (128, 128))

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = cv2.normalize(hist, hist).flatten()

    lbp = local_binary_pattern(gray, 8, 1, method="uniform")
    lbp_hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 59))
    lbp_hist = lbp_hist.astype("float")
    lbp_hist /= (lbp_hist.sum() + 1e-6)

    hog_feat = hog(
        gray,
        orientations=9,
        pixels_per_cell=(16, 16),
        cells_per_block=(2, 2),
        block_norm="L2-Hys"
    )

    return np.concatenate([hist, lbp_hist, hog_feat])

def similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

# ======================================================
# LOAD DATASET
# ======================================================
known_features = []
student_ids = []

DATASET_DIR = "dataset"

for sid in os.listdir(DATASET_DIR):
    folder = os.path.join(DATASET_DIR, sid)
    if not os.path.isdir(folder):
        continue

    images = os.listdir(folder)
    if not images:
        continue

    img = cv2.imread(os.path.join(folder, images[0]))
    if img is None:
        continue

    known_features.append(extract_features(img))
    student_ids.append(sid)

# ======================================================
# MEDIAPIPE
# ======================================================
mp_face = mp.solutions.face_detection
mp_mesh = mp.solutions.face_mesh

face_detector = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.7)
face_mesh = mp_mesh.FaceMesh(refine_landmarks=True)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def eye_aspect_ratio(landmarks, eye):
    p = [np.array([landmarks[i].x, landmarks[i].y]) for i in eye]
    return (norm(p[1]-p[5]) + norm(p[2]-p[4])) / (2.0 * norm(p[0]-p[3]))

EAR_THRESHOLD = 0.20
RECOG_THRESHOLD = 0.75
blink_counter = {}

# ======================================================
# ATTENDANCE LOGIC
# ======================================================
def mark_attendance(student_id):
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT 1 FROM attendance WHERE student_id=? AND date=?",
        (student_id, today)
    )
    if cursor.fetchone():
        return

    now = datetime.now()
    cursor.execute(
        "INSERT INTO attendance VALUES (?, ?, ?)",
        (student_id, today, now.strftime("%H:%M:%S"))
    )
    conn.commit()

    cursor.execute(
        "SELECT name, class_name FROM students WHERE student_id=?",
        (student_id,)
    )
    name, cls = cursor.fetchone()

    status_label.config(
        text=f"✅ Attendance marked\n{name} ({cls})",
        fg="#059669"
    )

def export_csv():
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT s.student_id, s.name, s.class_name, a.time
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.date=?
    """, (today,))

    rows = cursor.fetchall()
    if not rows:
        return

    with open(f"attendance_{today}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Student ID", "Name", "Class", "Time"])
        writer.writerows(rows)

# ======================================================
# GUI
# ======================================================
root = tk.Tk()
root.title("Smart Attendance System")
root.geometry("1100x700")
root.configure(bg="#f4f6f8")
root.resizable(False, False)

# Header
tk.Label(
    root,
    text="Smart Attendance & Liveness Detection",
    font=("Segoe UI", 22, "bold"),
    bg="#1f2937",
    fg="white",
    pady=20
).pack(fill="x")

content = tk.Frame(root, bg="#f4f6f8")
content.pack(padx=20, pady=20, fill="both", expand=True)

video_label = tk.Label(content, bg="black")
video_label.grid(row=0, column=0, padx=10)

control = tk.Frame(content, bg="white", width=300)
control.grid(row=0, column=1, padx=20, sticky="n")

status_label = tk.Label(
    control,
    text="System Idle",
    font=("Segoe UI", 12),
    bg="white",
    fg="#374151",
    wraplength=260,
    justify="center"
)
status_label.pack(pady=20)

instruction = tk.Label(
    control,
    text="Instructions:\n• Start attendance\n• Look at camera\n• Blink to confirm\n• Attendance marked once",
    bg="white",
    fg="#6b7280",
    font=("Segoe UI", 11),
    justify="left"
)
instruction.pack(pady=10)

running = False
cap = None

# ======================================================
# CAMERA LOOP
# ======================================================
def update_frame():
    if not running:
        return

    ret, frame = cap.read()
    if not ret:
        return

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_res = face_detector.process(rgb)
    mesh_res = face_mesh.process(rgb)

    if face_res.detections and mesh_res.multi_face_landmarks:
        for det, mesh in zip(face_res.detections, mesh_res.multi_face_landmarks):

            bbox = det.location_data.relative_bounding_box
            x, y = int(bbox.xmin * w), int(bbox.ymin * h)
            bw, bh = int(bbox.width * w), int(bbox.height * h)

            face = frame[y:y+bh, x:x+bw]
            if face.size == 0:
                continue

            feat = extract_features(face)
            scores = [similarity(feat, k) for k in known_features]
            idx = int(np.argmax(scores))
            score = scores[idx]

            if score > RECOG_THRESHOLD:
                sid = student_ids[idx]
                blink_counter[sid] = blink_counter.get(sid, 0)

                ear = (
                    eye_aspect_ratio(mesh.landmark, LEFT_EYE) +
                    eye_aspect_ratio(mesh.landmark, RIGHT_EYE)
                ) / 2

                if ear < EAR_THRESHOLD:
                    blink_counter[sid] += 1

                if blink_counter[sid] >= 2:
                    mark_attendance(sid)
                    cv2.rectangle(frame, (x,y), (x+bw,y+bh), (0,255,0), 2)
                else:
                    status_label.config(
                        text=f"Blink to confirm\n{sid}",
                        fg="#d97706"
                    )
            else:
                cv2.rectangle(frame, (x,y), (x+bw,y+bh), (0,0,255), 2)

    img = ImageTk.PhotoImage(
        Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((760, 460))
    )
    video_label.configure(image=img)
    video_label.image = img

    root.after(15, update_frame)

# ======================================================
# CONTROLS
# ======================================================
def start_system():
    global running, cap
    if running:
        return
    cap = cv2.VideoCapture(0)
    running = True
    status_label.config(
        text="System Running\nBlink to confirm liveness",
        fg="#2563eb"
    )
    update_frame()

def stop_system():
    global running
    running = False
    if cap:
        cap.release()
    export_csv()
    status_label.config(
        text="System stopped\nAttendance exported",
        fg="#059669"
    )
    messagebox.showinfo("Done", "Attendance CSV exported")

tk.Button(
    control,
    text="▶ Start Attendance",
    bg="#2563eb",
    fg="white",
    font=("Segoe UI", 12, "bold"),
    width=20,
    height=2,
    command=start_system
).pack(pady=10)

tk.Button(
    control,
    text="⏹ Stop & Export",
    bg="#dc2626",
    fg="white",
    font=("Segoe UI", 12, "bold"),
    width=20,
    height=2,
    command=stop_system
).pack(pady=10)

def on_close():
    stop_system()
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
