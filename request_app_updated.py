import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import qrcode
from PIL import Image, ImageTk

def init_db():
    conn = sqlite3.connect('requests.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 login TEXT NOT NULL UNIQUE,
                 password TEXT NOT NULL,
                 role TEXT NOT NULL CHECK(role IN ('admin', 'worker', 'client', 'manager')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS Equipment (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 serial_number TEXT NOT NULL UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS FaultTypes (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Requests (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date_added TEXT NOT NULL,
                 equipment_id INTEGER NOT NULL,
                 fault_type_id INTEGER NOT NULL,
                 description TEXT NOT NULL,
                 client_id INTEGER NOT NULL,
                 status TEXT NOT NULL,
                 worker_id INTEGER,
                 comments TEXT,
                 extended_deadline TEXT,
                 FOREIGN KEY (equipment_id) REFERENCES Equipment(id),
                 FOREIGN KEY (fault_type_id) REFERENCES FaultTypes(id),
                 FOREIGN KEY (client_id) REFERENCES Users(id),
                 FOREIGN KEY (worker_id) REFERENCES Users(id))''')
    
    c.execute("INSERT OR IGNORE INTO Users (login, password, role) VALUES ('admin1', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO Users (login, password, role) VALUES ('worker1', 'worker123', 'worker')")
    c.execute("INSERT OR IGNORE INTO Users (login, password, role) VALUES ('client1', 'client123', 'client')")
    c.execute("INSERT OR IGNORE INTO Users (login, password, role) VALUES ('manager1', 'manager123', 'manager')")
    c.execute("INSERT OR IGNORE INTO Equipment (name, serial_number) VALUES ('Printer', 'PR123')")
    c.execute("INSERT OR IGNORE INTO FaultTypes (name) VALUES ('Hardware Failure')")
    conn.commit()
    conn.close()

class RequestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Request Management System")
        self.current_user = None
        init_db()
        self.show_login()

    def show_login(self):
        self.clear_window()
        tk.Label(self.root, text="Login").pack()
        login_entry = tk.Entry(self.root)
        login_entry.pack()
        tk.Label(self.root, text="Password").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack()
        tk.Button(self.root, text="Login", command=lambda: self.login(login_entry.get(), password_entry.get())).pack()

    def login(self, login, password):
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        c.execute("SELECT * FROM Users WHERE login = ? AND password = ?", (login, password))
        user = c.fetchone()
        conn.close()
        if user:
            self.current_user = {'id': user[0], 'login': user[1], 'role': user[3]}
            messagebox.showinfo("Success", f"Welcome, {self.current_user['role']}!")
            self.show_main()
        else:
            messagebox.showerror("Error", "Invalid login or password")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_main(self):
        self.clear_window()
        if self.current_user['role'] == 'admin':
            tk.Button(self.root, text="Add Request", command=self.add_request).pack()
            tk.Button(self.root, text="Edit Request", command=self.edit_request).pack()
            tk.Button(self.root, text="View Requests", command=self.view_requests).pack()
            tk.Button(self.root, text="Search Request", command=self.search_request).pack()
            tk.Button(self.root, text="Statistics", command=self.show_statistics).pack()
            tk.Button(self.root, text="Generate QR Code", command=self.generate_qr_code).pack()
        elif self.current_user['role'] == 'worker':
            tk.Button(self.root, text="View Assigned Requests", command=self.view_requests).pack()
            tk.Button(self.root, text="Add Comment", command=self.add_comment).pack()
        elif self.current_user['role'] == 'client':
            tk.Button(self.root, text="Add Request", command=self.add_request).pack()
            tk.Button(self.root, text="View My Requests", command=self.view_requests).pack()
        elif self.current_user['role'] == 'manager':
            tk.Button(self.root, text="View All Requests", command=self.view_requests).pack()
            tk.Button(self.root, text="Extend Deadline", command=self.extend_deadline).pack()
            tk.Button(self.root, text="Assign Worker", command=self.assign_worker).pack()
            tk.Button(self.root, text="Add Consultation Note", command=self.add_consultation).pack()

    def add_request(self):
        self.clear_window()
        tk.Label(self.root, text="Equipment").pack()
        equipment_entry = tk.Entry(self.root)
        equipment_entry.pack()
        tk.Label(self.root, text="Fault Type").pack()
        fault_entry = tk.Entry(self.root)
        fault_entry.pack()
        tk.Label(self.root, text="Description").pack()
        desc_entry = tk.Entry(self.root)
        desc_entry.pack()
        tk.Button(self.root, text="Submit", command=lambda: self.submit_request(
            equipment_entry.get(), fault_entry.get(), desc_entry.get())).pack()

    def submit_request(self, equipment, fault, description):
        if not equipment or not fault or not description:
            messagebox.showerror("Error", "All fields are required!")
            return
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            c.execute("INSERT INTO Requests (date_added, equipment_id, fault_type_id, description, client_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (date_added, 1, 1, description, self.current_user['id'], 'pending'))
            conn.commit()
            messagebox.showinfo("Success", "Request added!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
        self.show_main()

    def view_requests(self):
        self.clear_window()
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        if self.current_user['role'] == 'client':
            c.execute("SELECT * FROM Requests WHERE client_id = ?", (self.current_user['id'],))
        elif self.current_user['role'] == 'worker':
            c.execute("SELECT * FROM Requests WHERE worker_id = ?", (self.current_user['id'],))
        else:
            c.execute("SELECT * FROM Requests")
        requests = c.fetchall()
        conn.close()
        
        tree = ttk.Treeview(self.root, columns=("ID", "Date", "Equipment", "Fault", "Description", "Status", "Deadline"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Date", text="Date")
        tree.heading("Equipment", text="Equipment")
        tree.heading("Fault", text="Fault Type")
        tree.heading("Description", text="Description")
        tree.heading("Status", text="Status")
        tree.heading("Deadline", text="Extended Deadline")
        for req in requests:
            tree.insert("", tk.END, values=(req[0], req[1], req[2], req[3], req[4], req[6], req[9] or "N/A"))
        tree.pack()
        tk.Button(self.root, text="Back", command=self.show_main).pack()

    def edit_request(self):
        self.clear_window()
        tk.Label(self.root, text="Request ID").pack()
        id_entry = tk.Entry(self.root)
        id_entry.pack()
        tk.Label(self.root, text="New Status").pack()
        status_entry = tk.Entry(self.root)
        status_entry.pack()
        tk.Button(self.root, text="Update", command=lambda: self.update_request(id_entry.get(), status_entry.get())).pack()

    def update_request(self, request_id, status):
        if not request_id.isdigit() or status not in ['pending', 'in_progress', 'completed']:
            messagebox.showerror("Error", "Invalid ID or status!")
            return
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        try:
            c.execute("UPDATE Requests SET status = ? WHERE id = ?", (status, request_id))
            conn.commit()
            messagebox.showinfo("Success", f"Request {request_id} updated to {status}!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
        self.show_main()

    def search_request(self):
        self.clear_window()
        tk.Label(self.root, text="Search by ID or Description").pack()
        search_entry = tk.Entry(self.root)
        search_entry.pack()
        tk.Button(self.root, text="Search", command=lambda: self.perform_search(search_entry.get())).pack()

    def perform_search(self, query):
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        c.execute("SELECT * FROM Requests WHERE id = ? OR description LIKE ?", (query, f"%{query}%"))
        requests = c.fetchall()
        conn.close()
        
        tree = ttk.Treeview(self.root, columns=("ID", "Date", "Equipment", "Fault", "Description", "Status", "Deadline"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Date", text="Date")
        tree.heading("Equipment", text="Equipment")
        tree.heading("Fault", text="Fault Type")
        tree.heading("Description", text="Description")
        tree.heading("Status", text="Status")
        tree.heading("Deadline", text="Extended Deadline")
        for req in requests:
            tree.insert("", tk.END, values=(req[0], req[1], req[2], req[3], req[4], req[6], req[9] or "N/A"))
        tree.pack()
        tk.Button(self.root, text="Back", command=self.show_main).pack()

    def show_statistics(self):
        self.clear_window()
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM Requests WHERE status = 'completed'")
        completed = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM Requests")
        total = c.fetchone()[0]
        c.execute("SELECT fault_type_id, COUNT(*) FROM Requests GROUP BY fault_type_id")
        fault_stats = c.fetchall()
        conn.close()

        tk.Label(self.root, text=f"Completed Requests: {completed}/{total}").pack()
        tk.Label(self.root, text="Fault Type Statistics:").pack()
        for stat in fault_stats:
            tk.Label(self.root, text=f"Fault ID {stat[0]}: {stat[1]} requests").pack()
        tk.Button(self.root, text="Back", command=self.show_main).pack()

    def add_comment(self):
        self.clear_window()
        tk.Label(self.root, text="Request ID").pack()
        id_entry = tk.Entry(self.root)
        id_entry.pack()
        tk.Label(self.root, text="Comment").pack()
        comment_entry = tk.Entry(self.root)
        comment_entry.pack()
        tk.Button(self.root, text="Submit", command=lambda: self.submit_comment(id_entry.get(), comment_entry.get())).pack()

    def submit_comment(self, request_id, comment):
        if not request_id.isdigit() or not comment:
            messagebox.showerror("Error", "Invalid ID or comment!")
            return
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        try:
            c.execute("UPDATE Requests SET comments = ? WHERE id = ?", (comment, request_id))
            conn.commit()
            messagebox.showinfo("Success", "Comment added!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
        self.show_main()

    def extend_deadline(self):
        self.clear_window()
        tk.Label(self.root, text="Request ID").pack()
        id_entry = tk.Entry(self.root)
        id_entry.pack()
        tk.Label(self.root, text="New Deadline (YYYY-MM-DD)").pack()
        deadline_entry = tk.Entry(self.root)
        deadline_entry.pack()
        tk.Button(self.root, text="Extend", command=lambda: self.submit_deadline(id_entry.get(), deadline_entry.get())).pack()

    def submit_deadline(self, request_id, deadline):
        if not request_id.isdigit() or not deadline:
            messagebox.showerror("Error", "Invalid ID or deadline!")
            return
        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
            return
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        try:
            c.execute("UPDATE Requests SET extended_deadline = ? WHERE id = ?", (deadline, request_id))
            conn.commit()
            messagebox.showinfo("Success", f"Deadline for request {request_id} extended to {deadline}!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
        self.show_main()

    def assign_worker(self):
        self.clear_window()
        tk.Label(self.root, text="Request ID").pack()
        id_entry = tk.Entry(self.root)
        id_entry.pack()
        tk.Label(self.root, text="Worker ID").pack()
        worker_id_entry = tk.Entry(self.root)
        worker_id_entry.pack()
        tk.Button(self.root, text="Assign", command=lambda: self.submit_worker(id_entry.get(), worker_id_entry.get())).pack()

    def submit_worker(self, request_id, worker_id):
        if not request_id.isdigit() or not worker_id.isdigit():
            messagebox.showerror("Error", "Invalid ID!")
            return
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        try:
            c.execute("SELECT id FROM Users WHERE role = 'worker' AND id = ?", (worker_id,))
            if not c.fetchone():
                messagebox.showerror("Error", "Invalid worker ID!")
                return
            c.execute("UPDATE Requests SET worker_id = ? WHERE id = ?", (worker_id, request_id))
            conn.commit()
            messagebox.showinfo("Success", f"Worker {worker_id} assigned to request {request_id}!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
        self.show_main()

    def add_consultation(self):
        self.clear_window()
        tk.Label(self.root, text="Request ID").pack()
        id_entry = tk.Entry(self.root)
        id_entry.pack()
        tk.Label(self.root, text="Consultation Note").pack()
        note_entry = tk.Entry(self.root)
        note_entry.pack()
        tk.Button(self.root, text="Submit", command=lambda: self.submit_consultation(id_entry.get(), note_entry.get())).pack()

    def submit_consultation(self, request_id, note):
        if not request_id.isdigit() or not note:
            messagebox.showerror("Error", "Invalid ID or note!")
            return
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        try:
            c.execute("UPDATE Requests SET comments = COALESCE(comments, '') || '\nConsultation: ' || ? WHERE id = ?", (note, request_id))
            conn.commit()
            messagebox.showinfo("Success", "Consultation note added!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
        self.show_main()

    def generate_qr_code(self):
        self.clear_window()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data("https://forms.gle/sample_feedback_form")  # Пример Google-формы
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save("feedback_qr.png")
        
        qr_img = Image.open("feedback_qr.png")
        qr_img = qr_img.resize((200, 200))
        qr_photo = ImageTk.PhotoImage(qr_img)
        tk.Label(self.root, image=qr_photo).pack()
        tk.Label(self.root, text="Scan to leave feedback").pack()
        tk.Button(self.root, text="Back", command=self.show_main).pack()
        self.root.qr_photo = qr_photo  # Сохраняем ссылку, чтобы избежать сборки мусора

# Запуск приложения
root = tk.Tk()
app = RequestApp(root)
root.mainloop()