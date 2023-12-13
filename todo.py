import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="todo"
        )
        if connection.is_connected():
            print("Connected to the database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def create_tables(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS uzivatel (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255), password VARCHAR(255))")
        cursor.execute("CREATE TABLE IF NOT EXISTS ukol (id INT AUTO_INCREMENT PRIMARY KEY, nazev VARCHAR(255), popis TEXT, datum_cas DATE, splneno BOOLEAN)")
        cursor.execute("CREATE TABLE IF NOT EXISTS uzivatel_ukol (uzivatel_id INT, ukol_id INT, FOREIGN KEY (uzivatel_id) REFERENCES uzivatel(id), FOREIGN KEY (ukol_id) REFERENCES ukol(id), PRIMARY KEY (uzivatel_id, ukol_id))")
        connection.commit()
        print("Tables created successfully")
    except Error as e:
        print(f"Error: {e}")

def login(username, password, connection):
    hashed_password = hash_password(password)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM uzivatel WHERE username = %s AND password = %s", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            return user[0]
        else:
            return None
    except Error as e:
        print(f"Error: {e}")
        return None

def add_task(nazev, popis, deadline, user_id, connection):
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO ukol (nazev, popis, datum_cas, splneno) VALUES (%s, %s, %s, %s)", (nazev, popis, deadline, 0))
        ukol_id = cursor.lastrowid
        cursor.execute("INSERT INTO uzivatel_ukol (uzivatel_id, ukol_id) VALUES (%s, %s)", (user_id, ukol_id))
        connection.commit()
        print("Task added successfully")
        return True
    except Error as e:
        print(f"Error: {e}")
        return False

def handle_login():
    global connection
    username = username_entry.get()
    password = password_entry.get()
    user_id = login(username, password, connection)
    if user_id is not None:
        login_window.destroy()
        show_todo_interface(user_id)
    else:
        messagebox.showerror("Error", "Invalid username or password")

def show_todo_interface(user_id):
    def add_task():
        nazev = nazev_entry.get()
        popis = popis_entry.get("1.0", tk.END)
        deadline = deadline_entry.get()

        if add_task_to_database(nazev, popis, deadline, user_id):
            messagebox.showinfo("Success", "Task added successfully")
            refresh_task_list()
        else:
            messagebox.showerror("Error", "Failed to add task")

    def mark_task_done():
        selected_item = task_tree.selection()
        if selected_item:
            task_id = task_tree.item(selected_item, "values")[0]
            if mark_task_as_done_in_database(task_id):
                messagebox.showinfo("Success", "Task marked as done")
                refresh_task_list()
            else:
                messagebox.showerror("Error", "Failed to mark task as done")

    def refresh_task_list():
        task_tree.delete(*task_tree.get_children())
        tasks = get_user_tasks(user_id)
        for task in tasks:
            task_tree.insert("", tk.END, values=task)

    def add_task_to_database(nazev, popis, deadline, user_id):
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO ukol (nazev, popis, datum_cas, splneno) VALUES (%s, %s, %s, %s)",
                           (nazev, popis, deadline, 0))
            ukol_id = cursor.lastrowid
            cursor.execute("INSERT INTO uzivatel_ukol (uzivatel_id, ukol_id) VALUES (%s, %s)", (user_id, ukol_id))
            connection.commit()
            return True
        except Error as e:
            print(f"Error: {e}")
            return False

    def get_user_tasks(user_id):
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT ukol.id, ukol.nazev, ukol.popis, ukol.datum_cas, ukol.splneno FROM ukol "
                           "JOIN uzivatel_ukol ON ukol.id = uzivatel_ukol.ukol_id "
                           "WHERE uzivatel_ukol.uzivatel_id = %s", (user_id,))
            tasks = cursor.fetchall()
            return tasks
        except Error as e:
            print(f"Error: {e}")
            return []

    def mark_task_as_done_in_database(task_id):
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE ukol SET splneno = %s WHERE id = %s", (1, task_id))
            connection.commit()
            return True
        except Error as e:
            print(f"Error: {e}")
            return False

    def delete_task():
        selected_item = task_tree.selection()
        if selected_item:
            task_id = task_tree.item(selected_item, "values")[0]
            print(f"Selected task ID for deletion: {task_id}")
            if delete_task_from_database(task_id):
                messagebox.showinfo("Success", "Task deleted successfully")
                refresh_task_list()
            else:
                messagebox.showerror("Error", "Failed to delete task")


    def delete_task_from_database(task_id):
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM ukol WHERE id = %s", (task_id,))
            cursor.execute("DELETE FROM uzivatel_ukol WHERE ukol_id = %s", (task_id,))
            connection.commit()
            print(f"Task {task_id} deleted successfully")
            return True
        except Error as e:
            print(f"Error: {e}")
            return False


    todo_window = tk.Tk()
    todo_window.title("TODO App")

    nazev_label = tk.Label(todo_window, text="Název úkolu:")
    nazev_entry = tk.Entry(todo_window)
    popis_label = tk.Label(todo_window, text="Popis úkolu:")
    popis_entry = tk.Text(todo_window, height=4, width=40)
    deadline_label = tk.Label(todo_window, text="Datum dokončení(deadline)'YY-MM-DD':")
    deadline_entry = tk.Entry(todo_window)

    add_task_button = tk.Button(todo_window, text="Přidat úkol", command=add_task)
    mark_done_button = tk.Button(todo_window, text="Označit jako dokončený", command=mark_task_done)
    delete_task_button = tk.Button(todo_window, text="Smazat úkol", command=delete_task)

    task_tree = ttk.Treeview(todo_window, columns=("ID", "Name", "Description", "Deadline", "Done"), show="headings", selectmode="browse")
    task_tree.heading("ID", text="ID")
    task_tree.heading("Name", text="Název úkolu")
    task_tree.heading("Description", text="Popis úkolu")
    task_tree.heading("Deadline", text="Deadline")
    task_tree.heading("Done", text="Dokončen")

    refresh_task_list()

    nazev_label.grid(row=0, column=0, sticky=tk.E)
    nazev_entry.grid(row=0, column=1)
    popis_label.grid(row=1, column=0, sticky=tk.E)
    popis_entry.grid(row=1, column=1)
    deadline_label.grid(row=2, column=0, sticky=tk.E)
    deadline_entry.grid(row=2, column=1)
    add_task_button.grid(row=3, column=0, columnspan=2)
    mark_done_button.grid(row=4, column=0, columnspan=2)
    delete_task_button.grid(row=5, column=0, columnspan=2)
    task_tree.grid(row=6, column=0, columnspan=2)

    todo_window.mainloop()

connection = connect_to_database()

if connection:
    create_tables(connection)

    login_window = tk.Tk()
    login_window.title("Login")

    username_label = tk.Label(login_window, text="Username:")
    password_label = tk.Label(login_window, text="Password:")

    username_entry = tk.Entry(login_window)
    password_entry = tk.Entry(login_window, show="*")

    login_button = tk.Button(login_window, text="Login", command=handle_login)

    username_label.grid(row=0, column=0, sticky=tk.E)
    password_label.grid(row=1, column=0, sticky=tk.E)
    username_entry.grid(row=0, column=1)
    password_entry.grid(row=1, column=1)
    login_button.grid(columnspan=2)

    login_window.mainloop()
else:
    messagebox.showerror("Error", "Unable to connect to the database. Please check your connection settings.")
