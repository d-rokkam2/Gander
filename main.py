import sqlite3
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'
DATABASE = 'charterops.db'


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()  # or use FileHandler to log to a file
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# User model for authentication
class User(UserMixin):
    def __init__(self, id_, username, email, password):
        self.id = id_
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['email'], user['password'])
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# Routes for public pages
@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/flights')
@login_required
def flights():
    conn = get_db_connection()
    flights = conn.execute('SELECT * FROM flights ORDER BY departure_time').fetchall()
    conn.close()

    # Log the access event with the user's username
    logger.info(f"User {current_user.username} accessed flight schedule.")

    return render_template('flights.html', flights=flights)


@app.route('/add_flight', methods=['GET', 'POST'])
@login_required
def add_flight():
    if request.method == 'POST':
        pilot_name = request.form['pilot_name']
        flight_number = request.form['flight_number']
        departure_time = request.form['departure_time']
        origin = request.form['origin']
        destination = request.form['destination']
        aircraft = request.form['aircraft']
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO flights (pilot_name, flight_number, departure_time, origin, destination, aircraft) VALUES (?, ?, ?, ?, ?, ?)',
            (pilot_name, flight_number, departure_time, origin, destination, aircraft))
        conn.commit()
        conn.close()

        # Log the creation event with the user's username
        logger.info(f"User {current_user.username} added flight {flight_number}.")

        return redirect(url_for('flights'))
    return render_template('add_flight.html')


@app.route('/maintenance')
def maintenance():
    conn = get_db_connection()
    maints = conn.execute('SELECT * FROM maintenance ORDER BY due_date').fetchall()
    conn.close()
    return render_template('maintenance.html', maints=maints)


@app.route('/add_maintenance', methods=['GET', 'POST'])
def add_maintenance():
    if request.method == 'POST':
        aircraft = request.form['aircraft']
        description = request.form['description']
        due_date = request.form['due_date']  # e.g., "2025-04-15"
        conn = get_db_connection()
        conn.execute('INSERT INTO maintenance (aircraft, description, due_date) VALUES (?, ?, ?)',
                     (aircraft, description, due_date))
        conn.commit()
        conn.close()
        return redirect(url_for('maintenance'))
    return render_template('add_maintenance.html')


@app.route('/crew')
def crew():
    conn = get_db_connection()
    crew_members = conn.execute('SELECT * FROM crew').fetchall()
    conn.close()
    return render_template('crew.html', crew=crew_members)


@app.route('/add_crew', methods=['GET', 'POST'])
def add_crew():
    if request.method == 'POST':
        name = request.form['name']
        total_hours = float(request.form['total_hours'])
        last_flight = request.form.get('last_flight', None)
        # Flag as 'Needs Rest' if total hours exceed a threshold (e.g., 100)
        status = 'Needs Rest' if total_hours > 100 else 'OK'
        conn = get_db_connection()
        conn.execute('INSERT INTO crew (name, total_hours, last_flight, status) VALUES (?, ?, ?, ?)',
                     (name, total_hours, last_flight, status))
        conn.commit()
        conn.close()
        return redirect(url_for('crew'))
    return render_template('add_crew.html')


# User authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (username, email, password_hash))
            conn.commit()
        except Exception as e:
            conn.close()
            flash("Username or email already exists.")
            return redirect(url_for('register'))
        conn.close()
        flash("Account created! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['email'], user['password'])
            login_user(user_obj)
            flash("Logged in successfully.")
            return redirect(url_for('index'))
        flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/protected')
@login_required
def protected():
    return "You are logged in as " + current_user.username

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('index'))


if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, pilot_name TEXT NOT NULL, flight_number TEXT NOT NULL, departure_time TEXT NOT NULL, origin TEXT NOT NULL, destination TEXT NOT NULL, aircraft TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY AUTOINCREMENT, aircraft TEXT NOT NULL, description TEXT NOT NULL, due_date TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS crew (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, total_hours REAL NOT NULL, last_flight TEXT, status TEXT DEFAULT 'OK')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    conn.commit()
    conn.close()
    app.run(debug=True)