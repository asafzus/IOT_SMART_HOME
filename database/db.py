import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'baby_room.db')


def create_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            relay_status TEXT,
            alert_level TEXT,
            alert_message TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_reading(temperature, humidity, relay_status, alert_level, alert_message):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO readings (timestamp, temperature, humidity, relay_status, alert_level, alert_message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temperature, humidity, relay_status, alert_level, alert_message))
    conn.commit()
    conn.close()


def get_recent(n=20):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, temperature, humidity, relay_status, alert_level, alert_message FROM readings ORDER BY id DESC LIMIT ?', (n,))
    rows = cursor.fetchall()
    conn.close()
    return rows
