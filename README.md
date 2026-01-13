# Smart Attendance & Proxy Detection System

A complete **Python-based smart attendance system** that uses **face recognition with blink-based liveness detection**, along with a **full Admin Dashboard**. The system is designed to solve real-world attendance problems while following ethical and scalable software practices.

---

## 🚀 Key Features

### 🧑‍💼 Admin Dashboard

* Central control panel for the system
* Launch student registration and attendance modules
* View all registered students
* Search and delete students (database + face data)
* Export daily attendance reports (CSV)

### 🎓 Student Registration

* Register students with:

  * Student ID
  * Full Name
  * Class / Section
* Capture face images via webcam
* Automatic dataset folder creation
* Auto-reset after each successful registration

### 👩‍🏫 Attendance System

* Real-time face detection using MediaPipe
* Face recognition using hybrid features (Histogram + LBP + HOG)
* Blink-based liveness detection to prevent proxy attendance
* Attendance marked **once per day per student**
* Clean GUI for teachers
* Automatic CSV export

### 🧠 Engineering Highlights

* Modular architecture (Admin / Registration / Attendance)
* SQLite database for persistence
* Virtual environment–safe execution
* Privacy-aware (no biometric data pushed to GitHub)
* GitHub-ready structure

---

## 🧱 Project Structure

```
SmartAttendanceSystem/
│
├── admin_dashboard.py        # Admin control panel
├── student_registration.py  # Student onboarding GUI
├── attendance_gui.py        # Attendance means GUI
│
├── dataset/                 # Face images (ignored in GitHub)
│   └── .gitkeep
│
├── attendance.db            # SQLite DB (ignored in GitHub)
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Tech Stack

* **Python 3.10+**
* **OpenCV** – camera handling
* **MediaPipe** – face detection & landmarks
* **Scikit-image** – feature extraction (LBP, HOG)
* **Tkinter** – desktop GUI
* **SQLite** – database

---

## 🛠️ Setup Instructions

### 1️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the System

Start from the **Admin Dashboard**:

```bash
python admin_dashboard.py
```

From there you can:

* Register students
* Start attendance
* Export reports

---

## 📄 Attendance Output

Attendance is exported as a CSV file:

```
attendance_YYYY-MM-DD.csv
```

Columns:

* Student ID
* Name
* Class
* Time

---

## 🔐 Privacy & Ethics

* Face images and database files are **excluded from GitHub**
* Intended for **educational and institutional use only**
* Consent must be obtained before collecting biometric data

---

## 🎯 Future Enhancements

* Role-based login (Admin / Teacher)
* Attendance analytics dashboard
* Subject-wise attendance
* Cloud database integration
* Executable (.exe) packaging

---

## 🏆 Author Note

This project was built to solve a **real-life problem**, not as a dummy or toy project. It demonstrates practical skills in **computer vision, GUI development, database design, and system integration**.

---


---

⭐ If you like this project, consider starring the repository!
