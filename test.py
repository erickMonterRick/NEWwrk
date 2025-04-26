from flask import Flask, render_template, request, redirect, session, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

DATABASE = 'chat.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''
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
    cur = db.cursor()
    
    if request.method == 'POST':
        message = request.form['message']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                    (session['username'], message, timestamp))
        db.commit()

    # Update query to include the `id` of each message
    cur.execute("SELECT id, username, message, timestamp FROM messages ORDER BY id DESC LIMIT 20")
    messages = cur.fetchall()
    messages.reverse()  # Show oldest first
    return render_template('chat.html', messages=messages, username=session['username'])

@app.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if 'username' not in session:
        return redirect('/')
    
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    db.commit()
    return redirect('/chat')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

