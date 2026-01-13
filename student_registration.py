import cv2
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# ================= DATABASE =================
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    class_name TEXT
)
""")
conn.commit()

# ================= GUI =================
root = tk.Tk()
root.title("Student Registration")
root.geometry("900x600")
root.configure(bg="#f4f6f8")
root.resizable(False, False)

# ---------- HEADER ----------
tk.Label(
    root,
    text="Student Registration Panel",
    font=("Segoe UI", 20, "bold"),
    bg="#1f2937",
    fg="white",
    pady=20
).pack(fill="x")

content = tk.Frame(root, bg="#f4f6f8")
content.pack(padx=20, pady=20, fill="both", expand=True)

# ---------- FORM ----------
form = tk.Frame(content, bg="white", padx=20, pady=20)
form.grid(row=0, column=0, padx=20)

tk.Label(form, text="Student ID", bg="white",
         font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", pady=5)
id_entry = tk.Entry(form, font=("Segoe UI", 12), width=25)
id_entry.grid(row=0, column=1, pady=5)

tk.Label(form, text="Full Name", bg="white",
         font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", pady=5)
name_entry = tk.Entry(form, font=("Segoe UI", 12), width=25)
name_entry.grid(row=1, column=1, pady=5)

tk.Label(form, text="Class / Section", bg="white",
         font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", pady=5)
class_entry = tk.Entry(form, font=("Segoe UI", 12), width=25)
class_entry.grid(row=2, column=1, pady=5)

# ---------- STATUS ----------
status_label = tk.Label(
    form,
    text="Fill details and capture 10 face images",
    bg="white",
    fg="#374151",
    font=("Segoe UI", 11)
)
status_label.grid(row=4, column=0, columnspan=2, pady=10)

# ---------- CAMERA ----------
video_frame = tk.Frame(content, bg="black")
video_frame.grid(row=0, column=1, padx=20)

video_label = tk.Label(video_frame)
video_label.pack()

cap = cv2.VideoCapture(0)

MAX_IMAGES = 10
captured = 0
current_student_id = None

# ---------- CAMERA LOOP ----------
def update_frame():
    ret, frame = cap.read()
    if not ret:
        return

    img = ImageTk.PhotoImage(
        Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((360, 270))
    )
    video_label.configure(image=img)
    video_label.image = img

    root.after(10, update_frame)

update_frame()

# ---------- RESET FORM ----------
def reset_form():
    global captured, current_student_id
    captured = 0
    current_student_id = None

    id_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    class_entry.delete(0, tk.END)

    status_label.config(
        text="✔ Registration complete. Ready for new student.",
        fg="#059669"
    )

# ---------- CAPTURE FACE ----------
def capture_face():
    global captured, current_student_id

    student_id = id_entry.get().strip()
    name = name_entry.get().strip()
    class_name = class_entry.get().strip()

    if not student_id or not name or not class_name:
        messagebox.showerror("Error", "Please fill all fields")
        return

    # Lock student_id for this session
    if current_student_id is None:
        current_student_id = student_id

        cursor.execute(
            "INSERT OR IGNORE INTO students VALUES (?, ?, ?)",
            (student_id, name, class_name)
        )
        conn.commit()

    # Prevent mixing students
    if student_id != current_student_id:
        messagebox.showwarning(
            "Warning",
            "Finish current registration before starting a new one"
        )
        return

    dataset_path = os.path.join("dataset", student_id)
    os.makedirs(dataset_path, exist_ok=True)

    ret, frame = cap.read()
    if not ret:
        return

    cv2.imwrite(
        os.path.join(dataset_path, f"{captured}.jpg"),
        frame
    )

    captured += 1
    status_label.config(
        text=f"Captured {captured}/{MAX_IMAGES}",
        fg="#2563eb"
    )

    if captured >= MAX_IMAGES:
        messagebox.showinfo(
            "Success",
            f"Student {student_id} registered successfully!"
        )
        reset_form()

# ---------- BUTTON ----------
tk.Button(
    form,
    text="Capture Face",
    font=("Segoe UI", 12, "bold"),
    bg="#2563eb",
    fg="white",
    width=20,
    height=2,
    command=capture_face
).grid(row=3, column=0, columnspan=2, pady=15)

# ---------- EXIT ----------
def on_close():
    cap.release()
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
