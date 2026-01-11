import cv2
import mediapipe as mp
import numpy as np
import os
import sqlite3
from datetime import datetime
from numpy.linalg import norm

# ----------------- DB SETUP -----------------
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    student_id TEXT,
    date TEXT,
    time TEXT
)
""")
conn.commit()

# ----------------- UTILS -----------------
def extract_features(face_img):
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (100, 100))
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    return cv2.normalize(hist, hist).flatten()

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

def already_marked(student_id, date):
    cursor.execute(
        "SELECT * FROM attendance WHERE student_id=? AND date=?",
        (student_id, date)
    )
    return cursor.fetchone() is not None

def mark_attendance(student_id):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if not already_marked(student_id, date):
        cursor.execute(
            "INSERT INTO attendance VALUES (?, ?, ?)",
            (student_id, date, time)
        )
        conn.commit()
        print(f"[ATTENDANCE] Marked: {student_id}")

# ----------------- LOAD DATASET -----------------
known_features = []
known_ids = []

DATASET_DIR = "dataset"

for student_id in os.listdir(DATASET_DIR):
    path = os.path.join(DATASET_DIR, student_id)
    if not os.path.isdir(path):
        continue

    img_path = os.path.join(path, os.listdir(path)[0])
    img = cv2.imread(img_path)
    if img is None:
        continue

    known_features.append(extract_features(img))
    known_ids.append(student_id)

print(f"[INFO] Loaded {len(known_ids)} students")

# ----------------- MEDIAPIPE -----------------
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.7
)

# ----------------- CAMERA -----------------
cap = cv2.VideoCapture(0)
THRESHOLD = 0.90
today = datetime.now().strftime("%Y-%m-%d")

# ----------------- MAIN LOOP -----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection.process(rgb)

    if results.detections:
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)

            face = frame[y:y+bh, x:x+bw]
            if face.size == 0:
                continue

            feat = extract_features(face)
            similarities = [cosine_similarity(feat, k) for k in known_features]

            best = np.argmax(similarities)
            score = similarities[best]

            label = "Unknown"
            color = (0, 0, 255)

            if score > THRESHOLD:
                label = known_ids[best]
                color = (0, 255, 0)
                mark_attendance(label)
            else:
                print("[PROXY ALERT] Unknown face detected")

            cv2.rectangle(frame, (x, y), (x+bw, y+bh), color, 2)
            cv2.putText(frame, label, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    cv2.imshow("Smart Attendance System", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
conn.close()
cv2.destroyAllWindows()
