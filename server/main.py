# server/main.py
import os, asyncio, json
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from server.database import init_db, get_db, DB_PATH
from server.routes import boxes, categories, box_detail, racks
from server.routes import rfid as rfid_routes
from server.routes import mobile as mobile_routes
from server.routes import ai_scan as ai_scan_routes
from server.mqtt import listener
from server.weather import poller as weather_poller
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
            # Push stored category back to the Feather
            async with db.execute("SELECT category FROM boxes WHERE box_id=?", (box_id,)) as cur:
                row = await cur.fetchone()
            if row and row["category"] and row["category"] != "Unassigned":
                listener.send_command(box_id, {"action": "set_category", "category": row["category"]})
                print(f"[server] Pushed category '{row['category']}' to {box_id} on boot")

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
    mqtt_broker = os.getenv("MQTT_BROKER", "192.168.4.47")
    mqtt_port   = int(os.getenv("MQTT_PORT", 1883))
    weather_poller.init(mqtt_broker, mqtt_port, ["box-01"])
    yield

app = FastAPI(title="SmartToolbox Server", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_BASE = Path(__file__).parent.parent
_CLIENT = _BASE / "client"

app.include_router(boxes.router)
app.include_router(categories.router)
app.include_router(box_detail.router)
app.include_router(racks.router)
app.include_router(rfid_routes.router)
app.include_router(mobile_routes.router)
app.include_router(ai_scan_routes.router)

app.mount("/client", StaticFiles(directory=str(_CLIENT)), name="client")

@app.get("/")
def root():
    return FileResponse(str(_CLIENT / "index.html"))

@app.get("/testing")
def testing_page():
    return FileResponse(str(_CLIENT / "testing.html"))

@app.get("/health")
def health():
    return {"status": "ok"}
