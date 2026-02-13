from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from datetime import datetime
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'edirt_secret_key_2024'

# Функции для работы с БД
def get_db():
    conn = sqlite3.connect('edirt.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Удаляем старую таблицу если она существует (для обновления структуры)
        conn.execute('DROP TABLE IF EXISTS users')
        conn.execute('DROP TABLE IF EXISTS posts')
        conn.execute('DROP TABLE IF EXISTS comments')
        conn.execute('DROP TABLE IF EXISTS likes')
        
        # Создаем таблицу пользователей с display_name
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица постов
        conn.execute('''
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица комментариев
        conn.execute('''
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица лайков
        conn.execute('''
            CREATE TABLE likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(post_id, user_id)
            )
        ''')
        
        # Создаем админа
        admin_password = hash_password('fima1456Game!')
        conn.execute('''
            INSERT INTO users (username, display_name, password, is_admin) 
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'Официальный Аккаунт Edirt', admin_password, 1))
        
        conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# HTML шаблоны
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edirt - Социальная сеть</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            text-decoration: none;
            color: #666;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: #667eea;
        }
        
        .admin-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .banned-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        
        .container {
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea.form-control {
            min-height: 120px;
            resize: vertical;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-small {
            padding: 8px 20px;
            font-size: 14px;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .btn-warning {
            background: #f39c12;
        }
        
        .btn-secondary {
            background: #999;
            margin-left: 10px;
        }
        
        .post {
            border-bottom: 1px solid #eee;
            padding: 25px 0;
            animation: slideIn 0.5s ease-out;
            position: relative;
        }
        
        .post:last-child {
            border-bottom: none;
        }
        
        .post.banned {
            opacity: 0.5;
            background: #fff5f5;
            padding: 25px;
            border-radius: 10px;
        }
        
        .post-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .post-author {
            font-weight: 600;
            color: #667eea;
            font-size: 1.1rem;
        }
        
        .post-author.admin {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .post-date {
            color: #999;
            font-size: 0.9rem;
        }
        
        .post-content {
            color: #444;
            line-height: 1.6;
            margin-bottom: 20px;
            font-size: 1.1rem;
        }
        
        .admin-actions {
            position: absolute;
            top: 25px;
            right: 0;
            display: flex;
            gap: 10px;
        }
        
        .admin-btn {
            padding: 5px 10px;
            font-size: 12px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            color: white;
            transition: transform 0.3s;
        }
        
        .admin-btn:hover {
            transform: scale(1.05);
        }
        
        .ban-user-btn {
            background: #e74c3c;
        }
        
        .ban-post-btn {
            background: #f39c12;
        }
        
        .unban-user-btn {
            background: #27ae60;
        }
        
        .unban-post-btn {
            background: #3498db;
        }
        
        .post-actions {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .like-btn {
            background: none;
            border: none;
            color: #e74c3c;
            font-size: 1.2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: transform 0.3s;
        }
        
        .like-btn:hover {
            transform: scale(1.1);
        }
        
        .like-btn.liked {
            color: #c0392b;
        }
        
        .comment-section {
            background: #f9f9f9;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .comment {
            padding: 15px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .comment:last-child {
            border-bottom: none;
        }
        
        .comment-author {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .comment-text {
            color: #666;
            line-height: 1.4;
        }
        
        .comment-date {
            font-size: 0.8rem;
            color: #999;
            margin-top: 5px;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
        
        .welcome-text {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .welcome-text h1 {
            font-size: 3rem;
            margin-bottom: 10px;
        }
        
        .welcome-text p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .empty-state {
            text-align: center;
            color: #999;
            padding: 40px;
        }
        
        .user-list {
            margin-top: 20px;
        }
        
        .user-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        
        .user-item:last-child {
            border-bottom: none;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .user-name {
            font-weight: 600;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">Edirt</a>
            <div class="nav-links">
                {% if session.user_id %}
                    {% if session.is_admin %}
                        <span class="admin-badge">Админ</span>
                        <a href="/admin/users">Управление пользователями</a>
                    {% endif %}
                    <a href="/create_post">+ Создать пост</a>
                    <a href="/logout">Выйти ({{ session.display_name or session.username }})</a>
                {% else %}
                    <a href="/login">Войти</a>
                    <a href="/register">Регистрация</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <!-- Основной контент -->
        <div class="welcome-text">
            <h1>Добро пожаловать в Edirt! 👋</h1>
            <p>Делитесь своими историями с миром</p>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 20px;">Последние истории</h2>
            
            {% if posts %}
                {% for post in posts %}
                    <div class="post">
                        {% if session.is_admin %}
                            <div class="admin-actions">
                                <form action="/admin/ban/user/{{ post.user_id }}" method="post" style="display: inline;">
                                    <button type="submit" class="admin-btn ban-user-btn">Забанить пользователя</button>
                                </form>
                                <form action="/admin/ban/post/{{ post.id }}" method="post" style="display: inline;">
                                    <button type="submit" class="admin-btn ban-post-btn">Забанить пост</button>
                                </form>
                            </div>
                        {% endif %}
                        
                        <div class="post-header">
                            <span class="post-author {% if post.is_admin %}admin{% endif %}">
                                {{ post.display_name or post.username }}
                                {% if post.is_admin %}
                                    <span class="admin-badge">Официальный</span>
                                {% endif %}
                            </span>
                            <span class="post-date">{{ post.created_at }}</span>
                        </div>
                        
                        <div class="post-content">{{ post.content }}</div>
                        
                        <div class="post-actions">
                            <form action="/like/{{ post.id }}" method="post" style="display: inline;">
                                <button type="submit" class="like-btn {% if post.user_liked %}liked{% endif %}" {% if session.user_banned %}disabled{% endif %}>
                                    ❤️ {{ post.likes }}
                                </button>
                            </form>
                        </div>
                        
                        <div class="comment-section">
                            <h3 style="margin-bottom: 15px;">Комментарии</h3>
                            
                            {% if post.comments %}
                                {% for comment in post.comments %}
                                    <div class="comment">
                                        <div class="comment-author">{{ comment.username }}</div>
                                        <div class="comment-text">{{ comment.content }}</div>
                                        <div class="comment-date">{{ comment.created_at }}</div>
                                    </div>
                                {% endfor %}
                            {% else %}
                                <p style="color: #999; text-align: center;">Пока нет комментариев</p>
                            {% endif %}
                            
                            {% if session.user_id and not session.user_banned %}
                                <form action="/comment/{{ post.id }}" method="post" style="margin-top: 20px;">
                                    <div class="form-group">
                                        <textarea name="content" class="form-control" placeholder="Напишите комментарий..." required></textarea>
                                    </div>
                                    <button type="submit" class="btn btn-small">Отправить</button>
                                </form>
                            {% elif session.user_banned %}
                                <p style="color: #e74c3c; text-align: center;">Ваш аккаунт забанен. Вы не можете оставлять комментарии.</p>
                            {% endif %}
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <p>Пока нет ни одной истории. Будьте первым!</p>
                    {% if session.user_id and not session.user_banned %}
                        <a href="/create_post" class="btn" style="display: inline-block; margin-top: 20px;">Создать пост</a>
                    {% endif %}
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

CREATE_POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edirt - Создать пост</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            text-decoration: none;
            color: #666;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: #667eea;
        }
        
        .admin-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .container {
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea.form-control {
            min-height: 120px;
            resize: vertical;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #999;
            margin-left: 10px;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">Edirt</a>
            <div class="nav-links">
                {% if session.user_id %}
                    {% if session.is_admin %}
                        <span class="admin-badge">Админ</span>
                        <a href="/admin/users">Управление пользователями</a>
                    {% endif %}
                    <a href="/create_post">+ Создать пост</a>
                    <a href="/logout">Выйти ({{ session.display_name or session.username }})</a>
                {% else %}
                    <a href="/login">Войти</a>
                    <a href="/register">Регистрация</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% if session.user_banned %}
            <div class="alert alert-warning">
                Ваш аккаунт забанен. Вы не можете создавать новые посты.
            </div>
        {% else %}
            <div class="card">
                <h2 style="margin-bottom: 20px;">Создать новую историю</h2>
                
                <form action="/create_post" method="post">
                    <div class="form-group">
                        <label for="content">Ваша история</label>
                        <textarea name="content" id="content" class="form-control" placeholder="Расскажите свою историю..." required></textarea>
                    </div>
                    <button type="submit" class="btn">Опубликовать</button>
                    <a href="/" class="btn btn-secondary">Отмена</a>
                </form>
            </div>
        {% endif %}
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edirt - Вход</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            text-decoration: none;
            color: #666;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: #667eea;
        }
        
        .container {
            max-width: 500px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .link {
            text-align: center;
            margin-top: 20px;
        }
        
        .link a {
            color: #667eea;
            text-decoration: none;
        }
        
        .link a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">Edirt</a>
            <div class="nav-links">
                {% if session.user_id %}
                    {% if session.is_admin %}
                        <span class="admin-badge">Админ</span>
                    {% endif %}
                    <a href="/create_post">+ Создать пост</a>
                    <a href="/logout">Выйти ({{ session.display_name or session.username }})</a>
                {% else %}
                    <a href="/login">Войти</a>
                    <a href="/register">Регистрация</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="card">
            <h2 style="margin-bottom: 20px; text-align: center;">Вход в Edirt</h2>
            
            <form action="/login" method="post">
                <div class="form-group">
                    <label for="username">Имя пользователя</label>
                    <input type="text" id="username" name="username" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="password">Пароль</label>
                    <input type="password" id="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn">Войти</button>
                <div class="link">
                    Нет аккаунта? <a href="/register">Зарегистрируйтесь</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edirt - Регистрация</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            text-decoration: none;
            color: #666;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: #667eea;
        }
        
        .container {
            max-width: 500px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .link {
            text-align: center;
            margin-top: 20px;
        }
        
        .link a {
            color: #667eea;
            text-decoration: none;
        }
        
        .link a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">Edirt</a>
            <div class="nav-links">
                {% if session.user_id %}
                    {% if session.is_admin %}
                        <span class="admin-badge">Админ</span>
                    {% endif %}
                    <a href="/create_post">+ Создать пост</a>
                    <a href="/logout">Выйти ({{ session.display_name or session.username }})</a>
                {% else %}
                    <a href="/login">Войти</a>
                    <a href="/register">Регистрация</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="card">
            <h2 style="margin-bottom: 20px; text-align: center;">Регистрация в Edirt</h2>
            
            <form action="/register" method="post">
                <div class="form-group">
                    <label for="username">Имя пользователя</label>
                    <input type="text" id="username" name="username" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="password">Пароль</label>
                    <input type="password" id="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn">Зарегистрироваться</button>
                <div class="link">
                    Уже есть аккаунт? <a href="/login">Войдите</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

ADMIN_USERS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edirt - Управление пользователями</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            text-decoration: none;
            color: #666;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: #667eea;
        }
        
        .admin-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        
        .container {
            max-width: 1000px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table th {
            text-align: left;
            padding: 15px;
            background: #f8f9fa;
            color: #555;
            font-weight: 600;
        }
        
        .table td {
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        
        .table tr:hover {
            background: #f8f9fa;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .btn-success {
            background: #27ae60;
        }
        
        .badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-admin {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .badge-banned {
            background: #e74c3c;
            color: white;
        }
        
        .badge-active {
            background: #27ae60;
            color: white;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">Edirt</a>
            <div class="nav-links">
                <span class="admin-badge">Админ</span>
                <a href="/admin/users">Управление пользователями</a>
                <a href="/create_post">+ Создать пост</a>
                <a href="/logout">Выйти ({{ session.display_name or session.username }})</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="card">
            <h2 style="margin-bottom: 20px;">Управление пользователями</h2>
            
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Имя пользователя</th>
                        <th>Отображаемое имя</th>
                        <th>Статус</th>
                        <th>Дата регистрации</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                        <tr>
                            <td>{{ user.id }}</td>
                            <td>{{ user.username }}</td>
                            <td>{{ user.display_name or '-' }}</td>
                            <td>
                                {% if user.is_admin %}
                                    <span class="badge badge-admin">Админ</span>
                                {% elif user.is_banned %}
                                    <span class="badge badge-banned">Забанен</span>
                                {% else %}
                                    <span class="badge badge-active">Активен</span>
                                {% endif %}
                            </td>
                            <td>{{ user.created_at }}</td>
                            <td>
                                {% if not user.is_admin %}
                                    {% if user.is_banned %}
                                        <form action="/admin/unban/user/{{ user.id }}" method="post" style="display: inline;">
                                            <button type="submit" class="btn btn-success">Разбанить</button>
                                        </form>
                                    {% else %}
                                        <form action="/admin/ban/user/{{ user.id }}" method="post" style="display: inline;">
                                            <button type="submit" class="btn btn-danger">Забанить</button>
                                        </form>
                                    {% endif %}
                                {% endif %}
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div style="margin-top: 20px;">
                <a href="/" class="btn">На главную</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Маршруты Flask
@app.route('/')
def index():
    with get_db() as conn:
        # Получаем все посты от незабаненных пользователей
        posts = conn.execute('''
            SELECT posts.*, users.username, users.display_name, users.is_admin, users.is_banned 
            FROM posts 
            JOIN users ON posts.user_id = users.id 
            WHERE users.is_banned = 0
            ORDER BY posts.created_at DESC
        ''').fetchall()
        
        posts_list = []
        for post in posts:
            comments = conn.execute('''
                SELECT comments.*, users.username 
                FROM comments 
                JOIN users ON comments.user_id = users.id 
                WHERE comments.post_id = ? 
                ORDER BY comments.created_at ASC
            ''', (post['id'],)).fetchall()
            
            likes_count = conn.execute('''
                SELECT COUNT(*) as count FROM likes WHERE post_id = ?
            ''', (post['id'],)).fetchone()['count']
            
            user_liked = False
            if session.get('user_id'):
                like = conn.execute('''
                    SELECT id FROM likes WHERE post_id = ? AND user_id = ?
                ''', (post['id'], session['user_id'])).fetchone()
                user_liked = like is not None
            
            posts_list.append({
                'id': post['id'],
                'user_id': post['user_id'],
                'username': post['username'],
                'display_name': post['display_name'],
                'is_admin': post['is_admin'],
                'content': post['content'],
                'created_at': post['created_at'],
                'comments': comments,
                'likes': likes_count,
                'user_liked': user_liked
            })
    
    return render_template_string(INDEX_TEMPLATE, posts=posts_list)

@app.route('/admin/users')
def admin_users():
    if not session.get('is_admin'):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    
    with get_db() as conn:
        users = conn.execute('''
            SELECT * FROM users ORDER BY created_at DESC
        ''').fetchall()
    
    return render_template_string(ADMIN_USERS_TEMPLATE, users=users)

@app.route('/admin/ban/user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    if not session.get('is_admin'):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    
    with get_db() as conn:
        conn.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (user_id,))
        conn.commit()
    
    flash('Пользователь забанен', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/unban/user/<int:user_id>', methods=['POST'])
def unban_user(user_id):
    if not session.get('is_admin'):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    
    with get_db() as conn:
        conn.execute('UPDATE users SET is_banned = 0 WHERE id = ?', (user_id,))
        conn.commit()
    
    flash('Пользователь разбанен', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/ban/post/<int:post_id>', methods=['POST'])
def ban_post(post_id):
    if not session.get('is_admin'):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    
    with get_db() as conn:
        conn.execute('UPDATE posts SET is_banned = 1 WHERE id = ?', (post_id,))
        conn.commit()
    
    flash('Пост забанен', 'success')
    return redirect(url_for('index'))

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if not session.get('user_id'):
        flash('Пожалуйста, войдите чтобы создать пост', 'error')
        return redirect(url_for('login'))
    
    if session.get('user_banned'):
        flash('Ваш аккаунт забанен. Вы не можете создавать посты', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        content = request.form['content']
        
        with get_db() as conn:
            conn.execute('''
                INSERT INTO posts (user_id, content) VALUES (?, ?)
            ''', (session['user_id'], content))
            conn.commit()
        
        flash('Ваша история опубликована!', 'success')
        return redirect(url_for('index'))
    
    return render_template_string(CREATE_POST_TEMPLATE)

@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if not session.get('user_id'):
        flash('Пожалуйста, войдите чтобы комментировать', 'error')
        return redirect(url_for('login'))
    
    if session.get('user_banned'):
        flash('Ваш аккаунт забанен. Вы не можете комментировать', 'error')
        return redirect(url_for('index'))
    
    content = request.form['content']
    
    with get_db() as conn:
        conn.execute('''
            INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)
        ''', (post_id, session['user_id'], content))
        conn.commit()
    
    flash('Комментарий добавлен!', 'success')
    return redirect(url_for('index'))

@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if not session.get('user_id'):
        flash('Пожалуйста, войдите чтобы ставить лайки', 'error')
        return redirect(url_for('login'))
    
    if session.get('user_banned'):
        flash('Ваш аккаунт забанен. Вы не можете ставить лайки', 'error')
        return redirect(url_for('index'))
    
    with get_db() as conn:
        existing_like = conn.execute('''
            SELECT id FROM likes WHERE post_id = ? AND user_id = ?
        ''', (post_id, session['user_id'])).fetchone()
        
        if existing_like:
            conn.execute('''
                DELETE FROM likes WHERE post_id = ? AND user_id = ?
            ''', (post_id, session['user_id']))
            flash('Лайк убран', 'success')
        else:
            conn.execute('''
                INSERT INTO likes (post_id, user_id) VALUES (?, ?)
            ''', (post_id, session['user_id']))
            flash('Лайк поставлен!', 'success')
        
        conn.commit()
    
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        with get_db() as conn:
            try:
                conn.execute('''
                    INSERT INTO users (username, password) VALUES (?, ?)
                ''', (username, password))
                conn.commit()
                flash('Регистрация успешна! Теперь вы можете войти', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Имя пользователя уже занято', 'error')
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        with get_db() as conn:
            user = conn.execute('''
                SELECT * FROM users WHERE username = ? AND password = ?
            ''', (username, password)).fetchone()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['display_name'] = user['display_name']
                session['is_admin'] = user['is_admin']
                session['user_banned'] = user['is_banned']
                
                if user['is_banned']:
                    flash('Ваш аккаунт забанен. Вы можете просматривать посты, но не можете создавать новые или комментировать', 'warning')
                else:
                    flash(f'Добро пожаловать, {user["display_name"] or user["username"]}!', 'success')
                
                return redirect(url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
