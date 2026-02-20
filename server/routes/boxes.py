# server/routes/boxes.py
from fastapi import APIRouter, Depends, HTTPException
from server.database import get_db
from server.models.box import BoxCommand
from server.mqtt import listener
from pydantic import BaseModel
from typing import Optional
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/api/boxes", tags=["boxes"])

@router.get("/")
async def list_boxes(db=Depends(get_db)):
    async with db.execute("SELECT * FROM boxes ORDER BY rack_id, box_id") as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]

@router.get("/{box_id}")
async def get_box(box_id: str, db=Depends(get_db)):
    async with db.execute("SELECT * FROM boxes WHERE box_id=?", (box_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, f"Box {box_id} not found")
    return dict(row)

class BoxPatch(BaseModel):
    display_name: Optional[str] = None
    zone: Optional[str] = None

@router.patch("/{box_id}")
async def patch_box(box_id: str, body: BoxPatch, db=Depends(get_db)):
    fields, vals = [], []
    if body.display_name is not None:
        fields.append("display_name=?"); vals.append(body.display_name)
    if body.zone is not None:
        fields.append("zone=?"); vals.append(body.zone)
    if not fields:
        raise HTTPException(400, "Nothing to update")
    vals.append(box_id)
    await db.execute(f"UPDATE boxes SET {', '.join(fields)} WHERE box_id=?", vals)
    await db.commit()
    return {"ok": True}

@router.post("/{box_id}/command")
async def send_command(box_id: str, cmd: BoxCommand, db=Depends(get_db)):
    listener.send_command(box_id, cmd.model_dump(exclude_none=True))
    # For set_category, also persist directly to DB so dashboard reflects immediately
    if cmd.action == "set_category" and cmd.category:
        await db.execute(
            "UPDATE boxes SET category=? WHERE box_id=?",
            (cmd.category, box_id)
        )
        await db.commit()
    return {"ok": True, "box_id": box_id, "command": cmd.action}

@router.get("/{box_id}/events")
async def get_events(box_id: str, limit: int = 50, db=Depends(get_db)):
    async with db.execute(
        "SELECT * FROM events WHERE box_id=? ORDER BY ts DESC LIMIT ?",
        (box_id, limit)
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]
