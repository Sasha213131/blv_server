from flask import Flask, request, jsonify
import sqlite3
import hashlib
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (email TEXT PRIMARY KEY,
                  password TEXT NOT NULL,
                  name TEXT NOT NULL,
                  username TEXT UNIQUE NOT NULL,
                  bio TEXT DEFAULT '')''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    username = data.get('username')

    if not email or not password or not name or not username:
        return jsonify({'error': 'Missing fields'}), 400

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email, password, name, username) VALUES (?, ?, ?, ?)',
                  (email, hash_password(password), name, username))
        conn.commit()
        # Возвращаем профиль без пароля
        user = {'id': email, 'name': name, 'username': username, 'bio': ''}
        return jsonify(user), 201
    except sqlite3.IntegrityError as e:
        return jsonify({'error': 'Email or username already exists'}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT name, username, bio FROM users WHERE email = ? AND password = ?',
              (email, hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        name, username, bio = row
        return jsonify({'id': email, 'name': name, 'username': username, 'bio': bio})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email, name, username, bio FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        email, name, username, bio = row
        return jsonify({'id': email, 'name': name, 'username': username, 'bio': bio})
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/users/<email>', methods=['PUT'])
def update_user(email):
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    bio = data.get('bio', '')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('UPDATE users SET name = ?, username = ?, bio = ? WHERE email = ?',
                  (name, username, bio, email))
        if c.rowcount == 0:
            return jsonify({'error': 'User not found'}), 404
        conn.commit()
        # Возвращаем обновлённый профиль
        return jsonify({'id': email, 'name': name, 'username': username, 'bio': bio})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already taken'}), 409
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)