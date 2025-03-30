from flask import Flask, render_template, request, redirect, url_for, abort
from pathlib import Path
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

DB_PATH = 'pastes.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pastes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                private BOOLEAN NOT NULL,
                views INTEGER DEFAULT 0,
                created TIMESTAMP NOT NULL
            )
        ''')

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        paste_id = str(uuid.uuid4())[:8]
        name = request.form['name']
        content = request.form['content']
        private = 'private' in request.form
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO pastes (id, name, content, private, created)
                VALUES (?, ?, ?, ?, ?)
            ''', (paste_id, name, content, private, datetime.now()))
        
        return redirect(url_for('view_paste', paste_id=paste_id))
    
    with sqlite3.connect(DB_PATH) as conn:
        public_pastes = conn.execute('''
            SELECT id, name, views FROM pastes 
            WHERE private = 0 
            ORDER BY created DESC 
            LIMIT 50
        ''').fetchall()
    
    return render_template('index.html', pastes=public_pastes)

@app.route('/<paste_id>')
def view_paste(paste_id):
    with sqlite3.connect(DB_PATH) as conn:
        paste = conn.execute('''
            UPDATE pastes SET views = views + 1 
            WHERE id = ? 
            RETURNING id, name, content, private, views, created
        ''', (paste_id,)).fetchone()
    
    if not paste:
        abort(404)
    
    return render_template('view.html', paste={
        'id': paste[0],
        'name': paste[1],
        'content': paste[2],
        'private': paste[3],
        'views': paste[4],
        'created': paste[5]
    })

@app.route('/<paste_id>/raw')
def raw_paste(paste_id):
    with sqlite3.connect(DB_PATH) as conn:
        content = conn.execute('''
            SELECT content FROM pastes WHERE id = ?
        ''', (paste_id,)).fetchone()
    
    if not content:
        abort(404)
    
    return render_template('raw.html', content=content[0])

if __name__ == '__main__':
    app.run(debug=True)