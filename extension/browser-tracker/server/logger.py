import json
import sqlite3
import os
from datetime import datetime

LOGS_DIR = 'logs'
TXT_FILE = os.path.join(LOGS_DIR, 'user_activity.txt')
JSON_FILE = os.path.join(LOGS_DIR, 'activity.json')
DB_FILE = os.path.join(LOGS_DIR, 'activity.db')

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            timestamp TEXT,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def log_event(event_type: str, timestamp: str, data: dict):
    # 1. Write to TXT (Human readable)
    with open(TXT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{event_type.upper()}]: {json.dumps(data)}\n")

    # 2. Write to JSON
    json_entry = {
        "type": event_type,
        "timestamp": timestamp,
        "data": data
    }
    # Append line to a JSONL file (technically activity.json here acts as JSONL)
    with open(JSON_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(json_entry) + '\n')

    # 3. Write to SQLite
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (type, timestamp, data) VALUES (?, ?, ?)",
            (event_type, timestamp, json.dumps(data))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging to SQLite: {e}")
