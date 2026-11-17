"""Small SQLite store. Only already-sanitised workflow state enters this boundary."""
import json
from contextlib import closing
import sqlite3
from pathlib import Path


class SessionStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, state TEXT NOT NULL)')

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def create(self, session_id, state):
        with closing(self.connect()) as db, db:
            db.execute('INSERT INTO sessions VALUES (?, ?)', (session_id, json.dumps(state)))

    def get(self, session_id):
        with closing(self.connect()) as db, db:
            row = db.execute('SELECT state FROM sessions WHERE id = ?', (session_id,)).fetchone()
        if not row:
            return None
        state = json.loads(row[0])
        state['_stored'] = row[0]
        return state

    def update(self, session_id, state):
        with closing(self.connect()) as db, db:
            expected = state.pop('_stored')
            cursor = db.execute('UPDATE sessions SET state = ? WHERE id = ? AND state = ?', (json.dumps(state), session_id, expected))
            return cursor.rowcount == 1
