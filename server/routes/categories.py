# server/routes/categories.py
from fastapi import APIRouter, Depends, HTTPException
from server.database import get_db
from server.models.category import Category, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("/")
async def list_categories(db=Depends(get_db)):
    async with db.execute("SELECT * FROM categories ORDER BY name") as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]

@router.post("/")
async def create_category(cat: Category, db=Depends(get_db)):
    try:
        await db.execute(
            "INSERT INTO categories (name, color, icon) VALUES (?, ?, ?)",
            (cat.name, cat.color, cat.icon)
        )
        await db.commit()
        return {"ok": True, "name": cat.name}
    except Exception:
        raise HTTPException(409, f"Category '{cat.name}' already exists")

@router.patch("/{name}")
async def update_category(name: str, update: CategoryUpdate, db=Depends(get_db)):
    fields = {k: v for k, v in update.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "No fields to update")
    sets = ", ".join(f"{k}=?" for k in fields)
    await db.execute(f"UPDATE categories SET {sets} WHERE name=?", (*fields.values(), name))
    await db.commit()
    return {"ok": True}

@router.delete("/{name}")
async def delete_category(name: str, db=Depends(get_db)):
    if name == "Unassigned":
        raise HTTPException(400, "Cannot delete default category")
    await db.execute("DELETE FROM categories WHERE name=?", (name,))
    await db.commit()
    return {"ok": True}
