import cv2
import mediapipe as mp
import numpy as np
import os
from numpy.linalg import norm

# ---------- UTILS ----------
def extract_features(face_img):
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (100, 100))

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return hist

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

# ---------- LOAD DATASET ----------
known_features = []
known_ids = []

DATASET_DIR = "dataset"

for student_id in os.listdir(DATASET_DIR):
    student_path = os.path.join(DATASET_DIR, student_id)

    if not os.path.isdir(student_path):
        continue

    images = os.listdir(student_path)
    if not images:
        continue

    img_path = os.path.join(student_path, images[0])
    img = cv2.imread(img_path)

    if img is None:
        continue

    feat = extract_features(img)
    known_features.append(feat)
    known_ids.append(student_id)

print(f"[INFO] Loaded {len(known_ids)} students")

# ---------- MEDIAPIPE ----------
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.7
)

# ---------- CAMERA ----------
cap = cv2.VideoCapture(0)

THRESHOLD = 0.90  # similarity threshold

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

            face_feat = extract_features(face)

            similarities = [
                cosine_similarity(face_feat, known)
                for known in known_features
            ]

            best_match = np.argmax(similarities)
            best_score = similarities[best_match]

            name = "Unknown"
            color = (0, 0, 255)

            if best_score > THRESHOLD:
                name = known_ids[best_match]
                color = (0, 255, 0)

            cv2.rectangle(frame, (x, y), (x+bw, y+bh), color, 2)
            cv2.putText(frame, f"{name} ({best_score:.2f})",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, color, 2)

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
