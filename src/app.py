from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(24))

db_path = os.path.join(os.path.dirname(__file__), "carpool.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS rides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER,
                car_name TEXT NOT NULL,
                start_location TEXT NOT NULL,
                end_location TEXT NOT NULL,
                date TEXT NOT NULL,
                seats INTEGER NOT NULL DEFAULT 4,
                price REAL NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (driver_id) REFERENCES users(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ride_id INTEGER,
                user_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ride_id) REFERENCES rides(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()

init_db()

# FIXED: ALL ROUTES DEFINED BEFORE HOME (critical for url_for to work)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['name']
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'danger')
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        with get_db() as conn:
            try:
                conn.execute(
                    'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                    (name, email, generate_password_hash(password))
                )
                conn.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Email already registered.', 'danger')
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get('username', 'User'))

@app.route("/logout")
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for("home"))

@app.route("/post_ride", methods=["GET", "POST"])
def post_ride():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        with get_db() as conn:
            conn.execute("""
                INSERT INTO rides (driver_id, car_name, start_location, end_location, date, seats, price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session['user_id'],
                request.form['car_name'],
                request.form['start_location'],
                request.form['end_location'],
                request.form['date'],
                int(request.form['seats']),
                float(request.form['price'])
            ))
            conn.commit()
            flash('Ride posted successfully!', 'success')
    return render_template("post_ride.html")

@app.route("/")
def home():  # NOW SAFE - all routes defined above
    return render_template("index.html")

# ... rest of your routes remain the same (search, book_ride, etc.) ...

@app.route("/search", methods=["GET", "POST"])
def search():
    rides = []
    if request.method == "POST":
        keyword = request.form.get("keyword")
        with get_db() as conn:
            rides = conn.execute("""
                SELECT * FROM rides 
                WHERE start_location LIKE ? OR end_location LIKE ?
                AND seats > 0
                ORDER BY created_at DESC
            """, (f"%{keyword}%", f"%{keyword}%")).fetchall()
    return render_template("search.html", rides=rides)

@app.route("/book_ride/<int:ride_id>", methods=["POST"])
def book_ride(ride_id):
    if "user_id" not in session:
        flash("Please log in to book a ride.", "warning")
        return redirect(url_for("login"))
    user_id = session["user_id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")
        cursor.execute("SELECT 1 FROM bookings WHERE user_id=? AND ride_id=?", (user_id, ride_id))
        if cursor.fetchone():
            conn.rollback()
            flash("You already booked this ride.", "info")
            return redirect(url_for("my_bookings"))
        cursor.execute("UPDATE rides SET seats = seats - 1 WHERE id = ? AND seats > 0", (ride_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            flash("No seats available or ride not found.", "danger")
            return redirect(url_for("search"))
        cursor.execute("INSERT INTO bookings (ride_id, user_id) VALUES (?, ?)", (ride_id, user_id))
        conn.commit()
    flash("Ride booked successfully!", "success")
    return redirect(url_for("my_bookings"))

@app.route("/my_bookings")
def my_bookings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    with get_db() as conn:
        bookings = conn.execute("""
            SELECT rides.*, bookings.created_at as booked_at
            FROM bookings
            JOIN rides ON rides.id = bookings.ride_id
            WHERE bookings.user_id=?
            ORDER BY bookings.created_at DESC
        """, (session["user_id"],)).fetchall()
    return render_template("my_bookings.html", bookings=bookings)

@app.route("/my_posted_rides")
def my_posted_rides():
    if "user_id" not in session:
        return redirect(url_for("login"))
    with get_db() as conn:
        rides = conn.execute("SELECT * FROM rides WHERE driver_id=? ORDER BY created_at DESC", (session["user_id"],)).fetchall()
    return render_template("my_posted_rides.html", rides=rides)

@app.route("/parts")
def parts():
    return "<h1>Parts - Coming Soon</h1>"

@app.route("/videos")
def videos():
    return "<h1>Videos - Coming Soon</h1>"

if __name__ == "__main__":
    app.run(debug=True)
