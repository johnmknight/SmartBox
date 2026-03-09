# server/routes/ai_scan.py
# AI-assisted inventory scan via Claude vision.
# POST /box/{box_id}/ai-scan — receives image, calls Claude, appends [AI] items to inventory.
import os, base64, json
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from server.database import get_db

router = APIRouter()

SCAN_DIR = Path("data/photos")
SCAN_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 2 * 1024 * 1024  # 2 MB cap before sending to Claude

_PROMPT = """You are analyzing a photograph of the open contents of a storage box or toolbox.

Identify every distinct item you can see. Return ONLY a valid JSON array of short item names.
One name per item. Be concise — use names like "Phillips screwdriver", "9V battery", "HDMI cable".
If you see multiples of the same item, include quantity in the name: "9V battery x3".
If the box appears empty or the image is unclear, return an empty array: []

Example output:
["tape measure", "Phillips screwdriver #2", "needle nose pliers", "9V battery x2"]

Return ONLY the JSON array. No explanation, no markdown fences."""

async def _call_claude(image_bytes: bytes, media_type: str) -> list[str]:
    """Send image to Claude vision, return list of detected item names."""
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)
    img_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": img_b64,
                    },
                },
                {"type": "text", "text": _PROMPT},
            ],
        }],
    )

    raw = message.content[0].text.strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        items = json.loads(raw)
        return [str(i).strip() for i in items if str(i).strip()]
    except json.JSONDecodeError:
        return []

@router.post("/box/{box_id}/ai-scan")
async def ai_scan(box_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    """
    Receive a photo, run Claude vision, append detected items to inventory.
    Items added by AI are prefixed with [AI] so the user can review on desktop.
    Returns the updated inventory text and the list of new items found.
    """
    # Verify box exists
    async with db.execute("SELECT inventory FROM boxes WHERE box_id=?", (box_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Box not found")

    # Read image
    image_bytes = await file.read()
    if len(image_bytes) > MAX_BYTES * 2:
        # Rough guard — PIL resize would be ideal but keeps deps minimal
        raise HTTPException(413, "Image too large (max 4MB)")

    # Determine media type
    ext = Path(file.filename or "photo.jpg").suffix.lower()
    mt_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
              ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
    media_type = mt_map.get(ext, "image/jpeg")

    # Save image (overwrites existing box photo — same as manual upload)
    dest = SCAN_DIR / f"{box_id}{ext}"
    dest.write_bytes(image_bytes)
    await db.execute("UPDATE boxes SET photo_path=? WHERE box_id=?", (str(dest), box_id))
    await db.commit()

    # Call Claude
    try:
        detected = await _call_claude(image_bytes, media_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"AI backend error: {e}")

    if not detected:
        return JSONResponse({"ok": True, "new_items": [], "inventory": row["inventory"] or "",
                             "message": "No items detected"})

    # Merge: only append items not already in inventory (case-insensitive match)
    existing_raw = row["inventory"] or ""
    existing_lines = {l.strip().lower() for l in existing_raw.splitlines() if l.strip()}

    new_lines = []
    for item in detected:
        # Strip [AI] prefix for comparison in case of re-scan
        clean = item.lower().removeprefix("[ai] ").strip()
        if clean not in existing_lines:
            new_lines.append(f"[AI] {item}")

    if not new_lines:
        return JSONResponse({"ok": True, "new_items": [], "inventory": existing_raw,
                             "message": "All detected items already in inventory"})

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    separator = f"\n# AI scan {ts}\n"
    updated = (existing_raw.rstrip() + separator + "\n".join(new_lines)).lstrip()

    await db.execute("UPDATE boxes SET inventory=? WHERE box_id=?", (updated, box_id))
    await db.commit()

    return JSONResponse({
        "ok": True,
        "new_items": new_lines,
        "inventory": updated,
        "message": f"{len(new_lines)} item(s) added"
    })
