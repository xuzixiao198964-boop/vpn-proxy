"""SQLite 用户：密码仅存储 PBKDF2-HMAC-SHA256 哈希。"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000, dklen=32)


class AuthStore:
    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def _init_db(self) -> None:
        with self._conn() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    salt BLOB NOT NULL,
                    pass_hash BLOB NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            row = c.execute("SELECT COUNT(*) FROM users").fetchone()
            if row and row[0] == 0:
                self._insert_user_unlocked(c, "demo", "demo123")

    def _insert_user_unlocked(self, c: sqlite3.Connection, username: str, password: str) -> None:
        salt = secrets.token_bytes(16)
        ph = _hash_password(password, salt)
        c.execute(
            "INSERT INTO users (username, salt, pass_hash) VALUES (?,?,?)",
            (username, salt, ph),
        )

    def verify(self, username: str, password: str) -> bool:
        with self._conn() as c:
            row = c.execute(
                "SELECT salt, pass_hash FROM users WHERE username=?",
                (username,),
            ).fetchone()
        if not row:
            return False
        salt, stored = row
        calc = _hash_password(password, salt)
        return hmac.compare_digest(calc, stored)

    def add_user(self, username: str, password: str) -> bool:
        try:
            with self._conn() as c:
                self._insert_user_unlocked(c, username, password)
            return True
        except sqlite3.IntegrityError:
            return False
