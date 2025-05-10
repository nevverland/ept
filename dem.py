import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Подключение к базе данных
def init_db():
    conn = sqlite3.connect('requests.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 login TEXT NOT NULL UNIQUE,
                 password TEXT NOT NULL,
                 role TEXT NOT NULL)''')
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
                 FOREIGN KEY (equipment_id) REFERENCES Equipment(id),
                 FOREIGN KEY (fault_type_id) REFERENCES FaultTypes(id),
                 FOREIGN KEY (client_id) REFERENCES Users(id),
                 FOREIGN KEY (worker_id) REFERENCES Users(id))''')
    
    # Добавление тестовых данных
    c.execute("INSERT OR IGNORE INTO Users (login, password, role) VALUES ('admin', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO Users (login, password, role) VALUES ('worker1', 'worker123', 'worker')")
    c.execute("INSERT OR IGNORE INTO Users (login, password, role) VALUES ('client1', 'client123', 'client')")
    c.execute("INSERT OR IGNORE INTO Equipment (name, serial_number) VALUES ('Printer', 'PR123')")
    c.execute("INSERT OR IGNORE INTO FaultTypes (name) VALUES ('Hardware Failure')")
    conn.commit()
    conn.close()

# Класс приложения
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
        elif self.current_user['role'] == 'worker':
            tk.Button(self.root, text="View Assigned Requests", command=self.view_requests).pack()
            tk.Button(self.root, text="Add Comment", command=self.add_comment).pack()
        elif self.current_user['role'] == 'client':
            tk.Button(self.root, text="Add Request", command=self.add_request).pack()
            tk.Button(self.root, text="View My Requests", command=self.view_requests).pack()

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
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO Requests (date_added, equipment_id, fault_type_id, description, client_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                  (date_added, 1, 1, description, self.current_user['id'], 'pending'))  # Упрощено: ID оборудования и неисправности фиксированы
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Request added!")
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
        
        tree = ttk.Treeview(self.root, columns=("ID", "Date", "Equipment", "Fault", "Description", "Status"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Date", text="Date")
        tree.heading("Equipment", text="Equipment")
        tree.heading("Fault", text="Fault Type")
        tree.heading("Description", text="Description")
        tree.heading("Status", text="Status")
        for req in requests:
            tree.insert("", tk.END, values=(req[0], req[1], req[2], req[3], req[4], req[6]))
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
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        c.execute("UPDATE Requests SET status = ? WHERE id = ?", (status, request_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Request {request_id} updated to {status}!")
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
        
        tree = ttk.Treeview(self.root, columns=("ID", "Date", "Equipment", "Fault", "Description", "Status"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Date", text="Date")
        tree.heading("Equipment", text="Equipment")
        tree.heading("Fault", text="Fault Type")
        tree.heading("Description", text="Description")
        tree.heading("Status", text="Status")
        for req in requests:
            tree.insert("", tk.END, values=(req[0], req[1], req[2], req[3], req[4], req[6]))
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
        conn = sqlite3.connect('requests.db')
        c = conn.cursor()
        c.execute("UPDATE Requests SET comments = ? WHERE id = ?", (comment, request_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Comment added!")
        self.show_main()

# Запуск приложения
root = tk.Tk()
app = RequestApp(root)
root.mainloop()