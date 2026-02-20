# server/main.py
import os, asyncio, json
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from server.database import init_db, get_db, DB_PATH
from server.routes import boxes, categories
from server.mqtt import listener
import aiosqlite

# -- DB update handler called by MQTT listener --
async def handle_mqtt(box_id: str, msg_type: str, payload: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now(timezone.utc).isoformat()

        if msg_type == "state":
            await db.execute("""
                INSERT INTO boxes (box_id, rack_id, display_name, state, category, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(box_id) DO UPDATE SET
                    state=excluded.state,
                    category=COALESCE(excluded.category, category),
                    last_seen=excluded.last_seen
            """, (
                box_id,
                payload.get("rack_id"),
                payload.get("display_name"),
                payload.get("state"),
                payload.get("category"),
                now,
            ))

        elif msg_type == "battery":
            await db.execute("""
                INSERT INTO boxes (box_id, battery_pct, battery_v, charging, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(box_id) DO UPDATE SET
                    battery_pct=excluded.battery_pct,
                    battery_v=excluded.battery_v,
                    charging=excluded.charging,
                    last_seen=excluded.last_seen
            """, (
                box_id,
                payload.get("pct"),
                payload.get("voltage"),
                1 if payload.get("charging") else 0,
                now,
            ))

        elif msg_type == "boot":
            await db.execute("""
                INSERT INTO boxes (box_id, rack_id, display_name, firmware, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(box_id) DO UPDATE SET
                    rack_id=excluded.rack_id,
                    display_name=excluded.display_name,
                    firmware=excluded.firmware,
                    last_seen=excluded.last_seen
            """, (
                box_id,
                payload.get("rack_id"),
                payload.get("display_name"),
                payload.get("version"),
                now,
            ))

        # Log all events
        await db.execute(
            "INSERT INTO events (box_id, event_type, payload, ts) VALUES (?, ?, ?, ?)",
            (box_id, msg_type, json.dumps(payload), now)
        )
        await db.commit()

# -- App lifespan --
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    listener.set_db_updater(handle_mqtt)
    loop = asyncio.get_event_loop()
    listener.start(loop)
    yield

app = FastAPI(title="SmartToolbox Server", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.include_router(boxes.router)
app.include_router(categories.router)

@app.get("/")
def root():
    return {"service": "SmartToolbox Server", "version": "1.0.0", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}
