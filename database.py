"""
database.py
------------
Database connection and schema for the Student Management System.

Runs on SQLite by default (zero configuration). A ready-to-use MySQL
version is included at the bottom of this file -- since your project
brief lists MySQL as part of the tech stack, switching takes only a
few minutes. See the README for step-by-step instructions.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "sms.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            address TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            course_code TEXT NOT NULL UNIQUE,
            duration TEXT,
            fee REAL NOT NULL DEFAULT 0,
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE(student_id, course_id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# MySQL VERSION (optional)
# ---------------------------------------------------------------------------
# To switch to MySQL:
#   1. pip install pymysql
#   2. CREATE DATABASE student_management_system;
#   3. Replace the SQLite code above with the block below (uncommented),
#      and update host / user / password to match your MySQL server.
#   4. No other file needs to change -- app.py only calls get_connection().
#
# import pymysql
# import pymysql.cursors
#
# DB_CONFIG = {
#     "host": "localhost",
#     "user": "root",
#     "password": "your_password",
#     "database": "student_management_system",
#     "cursorclass": pymysql.cursors.DictCursor,
# }
#
# def get_connection():
#     return pymysql.connect(**DB_CONFIG)
#
# def init_db():
#     conn = get_connection()
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             name VARCHAR(150) NOT NULL,
#             email VARCHAR(150) NOT NULL UNIQUE,
#             password_hash VARCHAR(255) NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     """)
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS students (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             first_name VARCHAR(100) NOT NULL,
#             last_name VARCHAR(100) NOT NULL,
#             email VARCHAR(150) NOT NULL UNIQUE,
#             phone VARCHAR(30),
#             address VARCHAR(255),
#             is_active TINYINT(1) NOT NULL DEFAULT 1,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
#         )
#     """)
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS courses (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             course_name VARCHAR(150) NOT NULL,
#             course_code VARCHAR(30) NOT NULL UNIQUE,
#             duration VARCHAR(50),
#             fee DECIMAL(10,2) NOT NULL DEFAULT 0,
#             description TEXT,
#             is_active TINYINT(1) NOT NULL DEFAULT 1,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
#         )
#     """)
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS enrollments (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             student_id INT NOT NULL,
#             course_id INT NOT NULL,
#             enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
#             FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
#             UNIQUE KEY unique_enrollment (student_id, course_id)
#         )
#     """)
#     conn.commit()
#     conn.close()
