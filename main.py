from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = 'charterops.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    # Dashboard homepage: links to flights and maintenance pages
    return render_template('index.html')


@app.route('/flights')
def flights():
    conn = get_db_connection()
    flights = conn.execute('SELECT * FROM flights ORDER BY departure_time').fetchall()
    conn.close()
    return render_template('flights.html', flights=flights)


@app.route('/add_flight', methods=['GET', 'POST'])
def add_flight():
    if request.method == 'POST':
        flight_number = request.form['flight_number']
        departure_time = request.form['departure_time']  # e.g., "2025-04-01 14:30"
        origin = request.form['origin']
        destination = request.form['destination']
        aircraft = request.form['aircraft']
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO flights (flight_number, departure_time, origin, destination, aircraft) VALUES (?, ?, ?, ?, ?)',
            (flight_number, departure_time, origin, destination, aircraft))
        conn.commit()
        conn.close()
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
        # Simple logic: if total hours exceed 100, mark as 'Needs Rest'
        status = 'Needs Rest' if total_hours > 100 else 'OK'
        conn = get_db_connection()
        conn.execute('INSERT INTO crew (name, total_hours, last_flight, status) VALUES (?, ?, ?, ?)',
                     (name, total_hours, last_flight, status))
        conn.commit()
        conn.close()
        return redirect(url_for('crew'))
    return render_template('add_crew.html')



if __name__ == '__main__':
    # Setup: create tables if they don't exist
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            aircraft TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aircraft TEXT NOT NULL,
            description TEXT NOT NULL,
            due_date TEXT NOT NULL
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS crew (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            total_hours REAL NOT NULL,
            last_flight TEXT,
            status TEXT DEFAULT 'OK'
        )
    ''')

    conn.commit()
    conn.close()

    app.run(debug=True)
