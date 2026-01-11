import cv2
import mediapipe as mp
import os

# ----------- INPUT -----------
student_id = input("Enter Student ID: ").strip()
SAVE_DIR = f"dataset/{student_id}"
os.makedirs(SAVE_DIR, exist_ok=True)

# ----------- MEDIAPIPE SETUP -----------
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.7
)

# ----------- CAMERA -----------
cap = cv2.VideoCapture(0)
count = 0
MAX_IMAGES = 10

print("Instructions:")
print("- Look straight, left, right, up, down")
print("- Press 'c' to capture image")
print("- Press ESC to exit")

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
            cv2.rectangle(frame, (x, y), (x+bw, y+bh), (0, 255, 0), 2)

            if cv2.waitKey(1) & 0xFF == ord('c') and face.size != 0:
                face_resized = cv2.resize(face, (224, 224))
                cv2.imwrite(f"{SAVE_DIR}/{count}.jpg", face_resized)
                print(f"[SAVED] Image {count}")
                count += 1

    cv2.putText(frame, f"Captured: {count}/{MAX_IMAGES}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2)

    cv2.imshow("Register Face", frame)

    if count >= MAX_IMAGES or cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

print("Face registration complete.")
