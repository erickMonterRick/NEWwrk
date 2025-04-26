from flask import Flask, render_template, request, redirect, session, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

DATABASE = 'chat.db'

# Database connection management
def get_db():
    if not hasattr(g, '_database'):
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row  # Allow dictionary-like access to rows
    return g._database

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()

# Initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        db.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect('/chat')
    return render_template('login.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor()

    # Handle message submission
    if request.method == 'POST':
        message = request.form['message']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
            (session['username'], message, timestamp)
        )
        db.commit()

    # Fetch messages with IDs for the front-end
    cursor.execute("SELECT id, username, message, timestamp FROM messages ORDER BY id DESC LIMIT 20")
    messages = cursor.fetchall()
    messages.reverse()  # Show messages in chronological order
    return render_template('chat.html', messages=messages, username=session['username'])

@app.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if 'username' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor()

    # Verify the logged-in user owns the message
    cursor.execute("SELECT username FROM messages WHERE id = ?", (message_id,))
    result = cursor.fetchone()
    if result and result['username'] == session['username']:
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        db.commit()

    return redirect('/chat')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
