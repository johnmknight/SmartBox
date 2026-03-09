# server/database.py
import os, aiosqlite
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/smarttoolbox.db")

async def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS boxes (
                box_id      TEXT PRIMARY KEY,
                rack_id     TEXT,
                display_name TEXT,
                state       TEXT DEFAULT 'UNKNOWN',
                category    TEXT DEFAULT 'Unassigned',
                battery_pct REAL DEFAULT -1,
                battery_v   REAL DEFAULT -1,
                charging    INTEGER DEFAULT 0,
                wifi_rssi   INTEGER,
                firmware    TEXT,
                last_seen   TEXT,
                inventory   TEXT DEFAULT '',
                photo_path  TEXT,
                zone        TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS racks (
                rack_id      TEXT PRIMARY KEY,
                display_name TEXT,
                zone         TEXT DEFAULT '',
                created_at   TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT UNIQUE NOT NULL,
                color       TEXT DEFAULT '#00D4FF',
                icon        TEXT DEFAULT 'tool',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                box_id      TEXT,
                event_type  TEXT,
                payload     TEXT,
                ts          TEXT DEFAULT (datetime('now'))
            )
        """)
        # Migrate existing DBs
        for col, defn in [
            ("inventory",    "TEXT DEFAULT ''"),
            ("photo_path",   "TEXT"),
            ("zone",                "TEXT DEFAULT ''"),
            ("last_rfid_accessed",  "DATETIME DEFAULT NULL"),
            ("rfid_provisioned",    "BOOLEAN DEFAULT 0"),
            ("rfid_provisioned_at", "DATETIME DEFAULT NULL"),
        ]:
            try:
                await db.execute(f"ALTER TABLE boxes ADD COLUMN {col} {defn}")
            except Exception:
                pass  # column already exists

        # Seed default categories
        await db.execute("""
            INSERT OR IGNORE INTO categories (name, color, icon) VALUES
                ('Unassigned',               '#555555', 'question-mark'),
                ('Hand Tools',               '#F59E0B', 'hammer'),
                ('Power Tools',              '#EF4444', 'bolt'),
                ('Measuring',                '#00D4FF', 'ruler'),
                ('Fasteners',                '#00FF80', 'screw'),
                ('Electrical',               '#A78BFA', 'plug'),
                ('Safety',                   '#FB923C', 'shield'),
                ('Art Supplies',             '#e879f9', 'palette'),
                ('3D Printing',              '#f97316', 'printer'),
                ('Parts',                    '#64748b', 'components'),
                ('Tools',                    '#eab308', 'tool'),
                ('Electronics - Raspberry Pi','#e11d48','cpu'),
                ('Electronics - Arduino',    '#06b6d4', 'circuit-board'),
                ('Electronics - Misc',       '#8b5cf6', 'plug'),
                ('Star Wars',                '#ffe81f', 'star'),
                ('Space',                    '#38bdf8', 'rocket'),
                ('Keyboards',               '#34d399', 'keyboard'),
                ('Tiki',                    '#f59e0b', 'tiki')
        """)
        await db.commit()
        print("[db] Database initialized")
