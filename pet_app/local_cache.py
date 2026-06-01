import json
import os
import sqlite3
import threading
from datetime import datetime

from app_paths import get_data_path

CACHE_DB = get_data_path("chat_cache.db")


def _connect():
    return sqlite3.connect(CACHE_DB)


def init_db():
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            tag TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_favorites_message_id ON favorites(message_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_favorites_tag ON favorites(tag)")
    conn.commit()
    conn.close()


def save_message(role, content):
    conn = _connect()
    c = conn.cursor()
    ts = datetime.now().isoformat()
    c.execute("INSERT INTO messages (role, content, timestamp, synced) VALUES (?, ?, ?, 0)",
              (role, content, ts))
    conn.commit()
    msg_id = c.lastrowid
    conn.close()
    return msg_id, ts


def get_all_messages():
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messages ORDER BY timestamp ASC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]} for r in rows]


def get_messages_by_date(date_str):
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messages WHERE timestamp LIKE ? ORDER BY timestamp ASC",
              (f"{date_str}%",))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]} for r in rows]


def delete_message(msg_id):
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE message_id = ?", (msg_id,))
    c.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def delete_messages_by_date(date_str):
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE message_id IN (SELECT id FROM messages WHERE timestamp LIKE ?)",
              (f"{date_str}%",))
    c.execute("DELETE FROM messages WHERE timestamp LIKE ?", (f"{date_str}%",))
    conn.commit()
    conn.close()


def get_dates_with_messages():
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT DISTINCT substr(timestamp, 1, 10) FROM messages ORDER BY timestamp ASC")
    rows = c.fetchall()
    conn.close()
    return set(r[0] for r in rows)


def get_unsynced_messages():
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messages WHERE synced = 0 ORDER BY timestamp ASC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]} for r in rows]


def mark_synced(msg_id):
    conn = _connect()
    c = conn.cursor()
    c.execute("UPDATE messages SET synced = 1 WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def add_favorite(message_id, tag=""):
    conn = _connect()
    c = conn.cursor()
    ts = datetime.now().isoformat()
    c.execute("INSERT INTO favorites (message_id, tag, created_at) VALUES (?, ?, ?)",
              (message_id, tag, ts))
    conn.commit()
    fid = c.lastrowid
    conn.close()
    return fid


def remove_favorite(fav_id):
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE id = ?", (fav_id,))
    conn.commit()
    conn.close()


def remove_favorite_by_message_id(message_id):
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE message_id = ?", (message_id,))
    conn.commit()
    conn.close()


def is_favorite(message_id):
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM favorites WHERE message_id = ?", (message_id,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0


def get_favorites(tag=None):
    conn = _connect()
    c = conn.cursor()
    if tag:
        c.execute("""
            SELECT f.id, f.message_id, f.tag, f.created_at,
                   m.role, m.content, m.timestamp
            FROM favorites f
            JOIN messages m ON f.message_id = m.id
            WHERE f.tag = ?
            ORDER BY f.created_at DESC
        """, (tag,))
    else:
        c.execute("""
            SELECT f.id, f.message_id, f.tag, f.created_at,
                   m.role, m.content, m.timestamp
            FROM favorites f
            JOIN messages m ON f.message_id = m.id
            ORDER BY f.created_at DESC
        """)
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0], "message_id": r[1], "tag": r[2], "created_at": r[3],
        "role": r[4], "content": r[5], "timestamp": r[6]
    } for r in rows]


def get_all_tags():
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT DISTINCT tag FROM favorites WHERE tag != '' ORDER BY tag")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


init_db()