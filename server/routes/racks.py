# server/routes/racks.py
from fastapi import APIRouter, Depends, HTTPException
from server.database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/racks", tags=["racks"])

class RackCreate(BaseModel):
    rack_id: str
    display_name: Optional[str] = None
    zone: Optional[str] = None

class RackPatch(BaseModel):
    display_name: Optional[str] = None
    zone: Optional[str] = None

@router.get("/")
async def list_racks(db=Depends(get_db)):
    async with db.execute("SELECT DISTINCT rack_id FROM boxes WHERE rack_id IS NOT NULL") as cur:
        box_racks = [r[0] for r in await cur.fetchall()]
    for rid in box_racks:
        await db.execute(
            "INSERT OR IGNORE INTO racks (rack_id, display_name) VALUES (?, ?)",
            (rid, rid)
        )
    await db.commit()
    async with db.execute("SELECT * FROM racks ORDER BY rack_id") as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]

@router.post("/")
async def create_rack(body: RackCreate, db=Depends(get_db)):
    try:
        await db.execute(
            "INSERT INTO racks (rack_id, display_name, zone) VALUES (?, ?, ?)",
            (body.rack_id, body.display_name or body.rack_id, body.zone or '')
        )
        await db.commit()
    except Exception:
        raise HTTPException(409, f"Rack {body.rack_id} already exists")
    return {"ok": True, "rack_id": body.rack_id}

@router.get("/{rack_id}/boxes")
async def get_rack_boxes(rack_id: str, db=Depends(get_db)):
    async with db.execute(
        "SELECT * FROM boxes WHERE rack_id=? ORDER BY box_id", (rack_id,)
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]

@router.patch("/{rack_id}")
async def patch_rack(rack_id: str, body: RackPatch, db=Depends(get_db)):
    await db.execute(
        "INSERT OR IGNORE INTO racks (rack_id, display_name) VALUES (?, ?)",
        (rack_id, rack_id)
    )
    fields, vals = [], []
    if body.display_name is not None:
        fields.append("display_name=?"); vals.append(body.display_name)
    if body.zone is not None:
        fields.append("zone=?"); vals.append(body.zone)
    if fields:
        vals.append(rack_id)
        await db.execute(f"UPDATE racks SET {', '.join(fields)} WHERE rack_id=?", vals)
    await db.commit()
    return {"ok": True}

@router.delete("/{rack_id}")
async def delete_rack(rack_id: str, db=Depends(get_db)):
    await db.execute("DELETE FROM racks WHERE rack_id=?", (rack_id,))
    await db.commit()
    return {"ok": True}
