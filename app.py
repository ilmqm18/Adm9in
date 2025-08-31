from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "my_secret_key"

DATABASE = "database.db"

# ---------------- DB CONNECT ----------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INIT DB ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Table users
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    # Table content (เก็บหลาย record)
    cur.execute('''CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )''')
    conn.commit()

    # Insert admin if not exists
    cur.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)",
                    ("admin", generate_password_hash("admin123")))
        conn.commit()
    conn.close()

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    conn = get_db()
    content_list = conn.execute("SELECT * FROM content ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", content_list=content_list)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()

    # เมื่อกด Submit เพื่อเพิ่ม content ใหม่
    if request.method == "POST":
        new_text = request.form["content"]
        conn.execute("INSERT INTO content (text) VALUES (?)", (new_text,))
        conn.commit()
        conn.close()
        flash("Content added successfully!")
        return redirect(url_for("dashboard"))

    # ดึงข้อมูลทั้งหมดมาแสดง
    content_list = conn.execute("SELECT * FROM content ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("dashboard.html", content_list=content_list)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    content = conn.execute("SELECT * FROM content WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        updated_text = request.form["content"]
        conn.execute("UPDATE content SET text=? WHERE id=?", (updated_text, id))
        conn.commit()
        conn.close()
        flash("Content updated successfully!")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit.html", content=content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
