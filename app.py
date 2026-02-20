from flask import Flask
app = Flask(__name__)
import os
os.makedirs('/tmp', exist_ok=True)
import yagmail
from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
from difflib import SequenceMatcher

app = Flask(__name__)
app.secret_key = "gla_secret"
app.config['UPLOAD_FOLDER'] = 'uploads'

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('/tmp/database.db')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll_no TEXT,
        course TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_email TEXT,
        item_name TEXT,
        description TEXT,
        category TEXT,
        image TEXT
    )
    ''')
    conn.commit()
    conn.close()----- EMAIL FUNCTION ----------------
def send_email(to_email, item_name):
    try:
        yag = yagmail.SMTP(
            "fitnesskavyansh@gmail.com",   # your gmail
            "kcio rkud bxdh vydk"           # your app password
        )

        yag.send(
            to_email,
            "GLA Lost & Found Confirmation",
            f"""
Dear Student,

Your item '{item_name}' has been successfully reported 
in GLA Digital Lost & Found System.

Regards,
GLA University
"""
        )

        print("Email sent successfully")

    except Exception as e:
        print("Email sending failed:", e)

# ---------------- HOME ----------------
@app.route('/')
def home():
    if 'student' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    items = conn.execute("SELECT * FROM items").fetchall()
    conn.close()
    return render_template('index.html', items=items)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    error = None

    if request.method == 'POST':
        try:
            conn = sqlite3.connect('database.db')
            conn.execute(
                "INSERT INTO students (name, roll_no, course, email, password) VALUES (?, ?, ?, ?, ?)",
                (request.form['name'],
                 request.form['roll_no'],
                 request.form['course'],
                 request.form['email'],
                 request.form['password'])
            )
            conn.commit()
            conn.close()
            return redirect('/login')

        except sqlite3.IntegrityError:
            error = "Email already registered!"

    return render_template('register.html', error=error)

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    error = None

    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        user = conn.execute(
            "SELECT * FROM students WHERE email=? AND password=?",
            (request.form['email'], request.form['password'])
        ).fetchone()
        conn.close()

        if user:
            session['student'] = user[4]
            return redirect('/')
        else:
            error = "Wrong Email or Password"

    return render_template('login.html', error=error)

# ---------------- ADD ITEM ----------------
@app.route('/add', methods=['POST'])
def add():
    if 'student' not in session:
        return redirect('/login')

    file = request.files['image']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = sqlite3.connect('database.db')
    conn.execute("INSERT INTO items (student_email, item_name, description, category, image) VALUES (?, ?, ?, ?, ?)",
                 (session['student'],
                  request.form['item_name'],
                  request.form['description'],
                  request.form['category'],
                  filename))
    conn.commit()
    conn.close()

    # 🔥 EMAIL SEND AFTER SUBMIT
    send_email(session['student'], request.form['item_name'])

    return redirect('/')

# ---------------- SEARCH ----------------
def similarity(a,b):
    return SequenceMatcher(None,a,b).ratio()

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    conn = sqlite3.connect('database.db')
    items = conn.execute("SELECT * FROM items").fetchall()
    conn.close()

    matched = []
    for item in items:
        if similarity(keyword.lower(), item[2].lower()) > 0.4:
            matched.append(item)

    return render_template('index.html', items=matched)

# ---------------- ADMIN ----------------
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        if request.form['username']=="admin" and request.form['password']=="gla123":
            session['admin']=True
            return redirect('/admin_dashboard')
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    conn = sqlite3.connect('database.db')
    items = conn.execute("SELECT * FROM items").fetchall()
    total = len(items)
    conn.close()
    return render_template('admin_dashboard.html', items=items, total=total)

# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():
    conn = sqlite3.connect('database.db')
    data = conn.execute("SELECT category, COUNT(*) FROM items GROUP BY category").fetchall()
    conn.close()
    return render_template('analytics.html', data=data)

# ---------------- UPLOADS ----------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
from flask import session, redirect, url_for

@app.route('/logout')
def logout():
    session.clear()   # session remove karega
    return redirect(url_for('login'))  # login page pe bhej dega



