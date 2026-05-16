from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import datetime
import uuid
import os
import re
import bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key_here_change_in_production")

# ── Database setup ─────────────────────────────────────────────────────────────
# Uses PostgreSQL if DATABASE_URL env var is set (e.g. on Render/Supabase),
# otherwise falls back to SQLite for local development.

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    def get_conn():
        url = DATABASE_URL
        # Render/Heroku give 'postgres://' but psycopg2 needs 'postgresql://'
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url, sslmode="require")

    def init_db():
        conn = get_conn()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                holder TEXT NOT NULL,
                number TEXT NOT NULL,
                expiry TEXT NOT NULL,
                cvv TEXT NOT NULL,
                FOREIGN KEY(username) REFERENCES users(username)
            )
        ''')
        conn.commit()
        conn.close()

    def load_users():
        conn = get_conn()
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute("SELECT username, password FROM users")
        users = {row['username']: {"password": row['password'], "cards": []} for row in c.fetchall()}
        c.execute("SELECT id, username, holder, number, expiry, cvv FROM cards")
        for row in c.fetchall():
            card = {"id": row['id'], "holder": row['holder'], "number": row['number'],
                    "expiry": row['expiry'], "cvv": row['cvv']}
            if row['username'] in users:
                users[row['username']]["cards"].append(card)
        conn.close()
        return users

    def save_user(username, password):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                  (username, hashed.decode('utf-8')))
        conn.commit()
        conn.close()

    def save_card(username, card):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO cards (id, username, holder, number, expiry, cvv) VALUES (%s,%s,%s,%s,%s,%s)",
                  (card['id'], username, card['holder'], card['number'], card['expiry'], card['cvv']))
        conn.commit()
        conn.close()

    def delete_user(username):
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM cards WHERE username = %s", (username,))
        c.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        conn.close()

    def delete_card(card_id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM cards WHERE id = %s", (card_id,))
        conn.commit()
        conn.close()

else:
    import sqlite3
    DB_FILE = os.path.join(os.path.dirname(__file__), "users.db")

    def get_conn():
        return sqlite3.connect(DB_FILE)

    def init_db():
        conn = get_conn()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                holder TEXT NOT NULL,
                number TEXT NOT NULL,
                expiry TEXT NOT NULL,
                cvv TEXT NOT NULL,
                FOREIGN KEY(username) REFERENCES users(username)
            )
        ''')
        conn.commit()
        conn.close()

    def load_users():
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT username, password FROM users")
        users = {row[0]: {"password": row[1], "cards": []} for row in c.fetchall()}
        c.execute("SELECT id, username, holder, number, expiry, cvv FROM cards")
        for row in c.fetchall():
            card = {"id": row[0], "holder": row[2], "number": row[3], "expiry": row[4], "cvv": row[5]}
            if row[1] in users:
                users[row[1]]["cards"].append(card)
        conn.close()
        return users

    def save_user(username, password):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hashed.decode('utf-8')))
        conn.commit()
        conn.close()

    def save_card(username, card):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO cards (id, username, holder, number, expiry, cvv) VALUES (?, ?, ?, ?, ?, ?)",
                  (card['id'], username, card['holder'], card['number'], card['expiry'], card['cvv']))
        conn.commit()
        conn.close()

    def delete_user(username):
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM cards WHERE username = ?", (username,))
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()

    def delete_card(card_id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()


# ── Helpers ────────────────────────────────────────────────────────────────────

def format_number(number):
    clean = number.replace(' ', '')
    return ' '.join([clean[i:i+4] for i in range(0, len(clean), 4)])

def validate_card(expiry):
    try:
        mm, yyyy = expiry.split('/')
        mm, yyyy = int(mm), int(yyyy)
        if yyyy < 100:
            yyyy += 2000
        today = datetime.date.today()
        return (yyyy > today.year) or (yyyy == today.year and mm >= today.month)
    except:
        return False

def mask_number(number):
    clean = number.replace(' ', '')
    return '**** **** **** ' + clean[-4:]

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is strong."

def validate_credit_card_number(number):
    """Validates card number using Luhn algorithm."""
    clean = number.replace(' ', '').replace('-', '')
    if not clean.isdigit() or len(clean) != 16:
        return False
    digits = [int(d) for d in clean]
    odd_sum = sum(digits[-1::-2])
    even_sum = sum(sum(divmod(d * 2, 10)) for d in digits[-2::-2])
    return (odd_sum + even_sum) % 10 == 0

def login(username, password):
    users = load_users()
    if username in users:
        hashed = users[username]["password"]
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    return False

def register(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    is_strong, msg = validate_password_strength(password)
    if not is_strong:
        return False, msg
    save_user(username, password)
    return True, "Account created successfully!"


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('landing'))

@app.route('/landing', methods=['GET', 'POST'])
def landing():
    if 'dev_mode' in session:
        return redirect(url_for('dev_dashboard'))
    dev_error = None
    if request.method == 'POST':
        key = request.form.get('dev_key', '')
        if key == 'upal140404':
            session['dev_mode'] = True
            return redirect(url_for('dev_dashboard'))
        else:
            dev_error = "Invalid developer key."
    return render_template('landing.html', dev_error=dev_error)

@app.route('/login', methods=['POST'])
def login_route():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if login(username, password):
        session['current_user'] = username
        flash(f"Welcome back, {username}!", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password.", "error")
        return redirect(url_for('landing'))

@app.route('/register', methods=['POST'])
def register_route():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        flash("Username and password cannot be empty!", "warning")
        return redirect(url_for('landing'))
    success, msg = register(username, password)
    if success:
        flash(msg, "success")
        return redirect(url_for('landing'))
    else:
        flash(msg, "error")
        return redirect(url_for('landing'))

@app.route('/logout')
def logout():
    session.pop('current_user', None)
    session.pop('dev_mode', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    if 'current_user' not in session:
        return redirect(url_for('landing'))
    users = load_users()
    user = session['current_user']
    card_count = len(users[user]["cards"])
    return render_template('dashboard.html', user=user, card_count=card_count)

@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if 'current_user' not in session:
        return redirect(url_for('landing'))
    if request.method == 'POST':
        holder = request.form.get('holder', '').strip()
        number = request.form.get('number', '').replace(" ", "").replace("-", "")
        expiry = request.form.get('expiry', '').strip()
        cvv = request.form.get('cvv', '').strip()
        if not all([holder, number, expiry, cvv]):
            flash("All fields are required.", "warning")
        elif not validate_credit_card_number(number):
            flash("Invalid card number. Only valid card numbers pass Luhn check.", "error")
        elif not cvv.isdigit() or len(cvv) != 3:
            flash("CVV must be exactly 3 digits.", "error")
        else:
            card = {
                "id": uuid.uuid4().hex,
                "holder": holder,
                "number": number,
                "expiry": expiry,
                "cvv": cvv,
            }
            save_card(session['current_user'], card)
            flash("Card saved successfully!", "success")
            return redirect(url_for('view_cards'))
    return render_template('add_card.html')

@app.route('/view_cards')
def view_cards():
    if 'current_user' not in session:
        return redirect(url_for('landing'))
    users = load_users()
    user = session['current_user']
    cards = users[user]["cards"]
    return render_template('view_cards.html', cards=cards, mask_number=mask_number)

@app.route('/card_details/<card_id>')
def card_details(card_id):
    if 'current_user' not in session:
        return redirect(url_for('landing'))
    users = load_users()
    user = session['current_user']
    cards = users[user]["cards"]
    card = next((c for c in cards if c['id'] == card_id), None)
    if not card:
        flash("Card not found.", "error")
        return redirect(url_for('view_cards'))
    return render_template('card_details.html', card=card, format_number=format_number)

@app.route('/check_validity/<card_id>')
def check_validity(card_id):
    if 'current_user' not in session:
        return redirect(url_for('landing'))
    users = load_users()
    user = session['current_user']
    cards = users[user]["cards"]
    card = next((c for c in cards if c['id'] == card_id), None)
    if not card:
        flash("Card not found.", "error")
        return redirect(url_for('view_cards'))
    if validate_card(card['expiry']):
        flash("Card is Valid!", "success")
    else:
        flash("Card has expired!", "error")
    return redirect(url_for('view_cards'))

@app.route('/delete_card/<card_id>', methods=['POST'])
def delete_card_route(card_id):
    if 'current_user' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    delete_card(card_id)
    return jsonify({'success': True, 'message': 'Card deleted'})

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if 'current_user' not in session:
        return redirect(url_for('landing'))
    if request.method == 'POST' and 'confirm' in request.form:
        delete_user(session['current_user'])
        session.pop('current_user')
        flash("Your account has been deleted.", "success")
        return redirect(url_for('landing'))
    return render_template('delete_account.html')

@app.route('/dev_dashboard', methods=['GET', 'POST'])
def dev_dashboard():
    if 'dev_mode' not in session:
        flash("Developer access required.", "error")
        return redirect(url_for('landing'))
    users_data = load_users()
    return render_template('dev_dashboard.html', users_data=users_data, format_number=format_number)

@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

init_db()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
