import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import os
import csv
from datetime import datetime
import shutil
import sys

# ================= DATABASE =================
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

# ================= GUI =================
root = tk.Tk()
root.title("Admin Dashboard – Smart Attendance System")
root.geometry("1000x650")
root.configure(bg="#f4f6f8")
root.resizable(False, False)

# ---------- HEADER ----------
tk.Label(
    root,
    text="Admin Dashboard",
    font=("Segoe UI", 22, "bold"),
    bg="#1f2937",
    fg="white",
    pady=20
).pack(fill="x")

# ---------- CONTENT ----------
content = tk.Frame(root, bg="#f4f6f8")
content.pack(padx=20, pady=20, fill="both", expand=True)

# ---------- LEFT PANEL ----------
left = tk.Frame(content, bg="white", width=300)
left.grid(row=0, column=0, sticky="n", padx=10)

tk.Label(left, text="Actions", font=("Segoe UI", 16, "bold"),
         bg="white").pack(pady=15)

def open_registration():
    subprocess.Popen([sys.executable, "student_registration.py"])

def open_attendance():
    subprocess.Popen([sys.executable, "attendance_gui.py"])

def export_today_attendance():
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT s.student_id, s.name, s.class_name, a.time
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.date=?
    """, (today,))
    rows = cursor.fetchall()

    if not rows:
        messagebox.showinfo("Info", "No attendance records today")
        return

    file = f"attendance_{today}.csv"
    with open(file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Student ID", "Name", "Class", "Time"])
        writer.writerows(rows)

    messagebox.showinfo("Exported", f"Attendance saved as {file}")

def styled_btn(text, cmd, color):
    return tk.Button(
        left,
        text=text,
        font=("Segoe UI", 12, "bold"),
        bg=color,
        fg="white",
        relief="flat",
        width=22,
        height=2,
        command=cmd
    )

styled_btn("➕ Register Student", open_registration, "#2563eb").pack(pady=8)
styled_btn("📸 Start Attendance", open_attendance, "#059669").pack(pady=8)
styled_btn("📤 Export Today CSV", export_today_attendance, "#7c3aed").pack(pady=8)

# ---------- RIGHT PANEL ----------
right = tk.Frame(content, bg="white")
right.grid(row=0, column=1, sticky="nsew", padx=10)

tk.Label(right, text="Registered Students",
         font=("Segoe UI", 16, "bold"),
         bg="white").pack(pady=15)

# ---------- SEARCH ----------
search_var = tk.StringVar()

search_entry = tk.Entry(
    right,
    textvariable=search_var,
    font=("Segoe UI", 12),
    width=30
)
search_entry.pack(pady=5)

# ---------- TABLE ----------
cols = ("Student ID", "Name", "Class")
tree = ttk.Treeview(right, columns=cols, show="headings", height=15)

for col in cols:
    tree.heading(col, text=col)
    tree.column(col, anchor="center", width=180)

tree.pack(pady=10)

# ---------- LOAD STUDENTS ----------
def load_students(filter_text=""):
    for row in tree.get_children():
        tree.delete(row)

    if filter_text:
        cursor.execute("""
            SELECT student_id, name, class_name
            FROM students
            WHERE student_id LIKE ? OR name LIKE ?
        """, (f"%{filter_text}%", f"%{filter_text}%"))
    else:
        cursor.execute("SELECT student_id, name, class_name FROM students")

    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

load_students()

def search_students(*args):
    load_students(search_var.get())

search_var.trace_add("write", search_students)

# ---------- DELETE STUDENT ----------
def delete_student():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a student first")
        return

    student_id = tree.item(selected[0])["values"][0]

    confirm = messagebox.askyesno(
        "Confirm",
        f"Delete student {student_id}?\nThis removes face data too."
    )
    if not confirm:
        return

    cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
    cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
    conn.commit()

    dataset_path = os.path.join("dataset", student_id)
    if os.path.exists(dataset_path):
        shutil.rmtree(dataset_path)

    load_students()
    messagebox.showinfo("Deleted", "Student removed successfully")

tk.Button(
    right,
    text="🗑 Delete Selected Student",
    bg="#dc2626",
    fg="white",
    font=("Segoe UI", 12, "bold"),
    width=25,
    height=2,
    command=delete_student
).pack(pady=10)

# ---------- EXIT ----------
def on_close():
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
