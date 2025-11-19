# backend/db.py
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "trajectories.sqlite3"
_db_lock = threading.Lock()

def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    cur = conn.cursor()
    # Performance pragmas for SQLite
    cur.executescript("""
    PRAGMA journal_mode = WAL;
    PRAGMA synchronous = NORMAL;
    PRAGMA temp_store = MEMORY;
    PRAGMA mmap_size = 300000000;
    """)
    # Trajectory table: add obstacles_json column
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trajectories (
        id TEXT PRIMARY KEY,
        name TEXT,
        created_at TEXT,
        min_x REAL,
        max_x REAL,
        min_y REAL,
        max_y REAL,
        length_m REAL,
        payload_json TEXT,
        obstacles_json TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bbox ON trajectories (min_x, max_x, min_y, max_y);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON trajectories (created_at);")
    # Ensure older DBs get the new column if missing (safe migration)
    cur.execute("PRAGMA table_info(trajectories);")
    cols = [r[1] for r in cur.fetchall()]
    if 'obstacles_json' not in cols:
        try:
            cur.execute("ALTER TABLE trajectories ADD COLUMN obstacles_json TEXT;")
        except Exception:
            # If alter fails for any reason, ignore - older rows will simply have no obstacles
            pass
    conn.commit()
    conn.close()

@contextmanager
def get_db_conn():
    """
    Returns a sqlite3 connection. Caller must not share across threads.
    We use a lock only around file-level operations where necessary.
    """
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False, timeout=30)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()
