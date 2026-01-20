import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection, init_db
from models import PasteCreate, PasteUpdate, PasteResponse, PasteListResponse
from auth import verify_token
from utils import generate_id, generate_name

app = FastAPI(title="Opnbin", description="A simple pastebin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/ping")
def ping(_: str = Depends(verify_token)):
    return {"message": "pong"}

def get_max_size() -> int:
    try:
        return int(os.environ.get("OPNBIN_MAX_SIZE", 1048576))
    except ValueError:
        return 1048576

@app.post("/", response_model=PasteResponse)
def create_paste(paste: PasteCreate, _: str = Depends(verify_token)):
    max_size = get_max_size()
    if len(paste.content.encode("utf-8")) > max_size:
        raise HTTPException(status_code=413, detail="content too large")

    paste_id = generate_id()
    name = paste.name or generate_name()
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO pastes (id, name, description, language, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (paste_id, name, paste.description, paste.language, paste.content, now, now)
    )
    conn.commit()
    conn.close()

    return PasteResponse(
        id=paste_id,
        name=name,
        description=paste.description,
        language=paste.language,
        content=paste.content,
        created_at=now,
        updated_at=now
    )

@app.get("/{paste_id}", response_model=PasteResponse)
def read_paste(paste_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM pastes WHERE id = ?", (paste_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="paste not found")

    return PasteResponse(**dict(row))

@app.put("/{paste_id}", response_model=PasteResponse)
def update_paste(paste_id: str, paste: PasteUpdate, _: str = Depends(verify_token)):
    conn = get_connection()
    row = conn.execute("SELECT * FROM pastes WHERE id = ?", (paste_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="paste not found")

    current = dict(row)
    updated_name = paste.name if paste.name is not None else current["name"]
    updated_description = paste.description if paste.description is not None else current["description"]
    updated_language = paste.language if paste.language is not None else current["language"]
    updated_content = paste.content if paste.content is not None else current["content"]

    if paste.content is not None:
        max_size = get_max_size()
        if len(updated_content.encode("utf-8")) > max_size:
            conn.close()
            raise HTTPException(status_code=413, detail="content too large")

    now = datetime.utcnow().isoformat()

    conn.execute(
        "UPDATE pastes SET name = ?, description = ?, language = ?, content = ?, updated_at = ? WHERE id = ?",
        (updated_name, updated_description, updated_language, updated_content, now, paste_id)
    )
    conn.commit()
    conn.close()

    return PasteResponse(
        id=paste_id,
        name=updated_name,
        description=updated_description,
        language=updated_language,
        content=updated_content,
        created_at=current["created_at"],
        updated_at=now
    )

@app.delete("/{paste_id}")
def delete_paste(paste_id: str, _: str = Depends(verify_token)):
    conn = get_connection()
    row = conn.execute("SELECT * FROM pastes WHERE id = ?", (paste_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="paste not found")

    conn.execute("DELETE FROM pastes WHERE id = ?", (paste_id,))
    conn.commit()
    conn.close()

    return {"message": "deleted"}

@app.get("/", response_model=PasteListResponse)
def list_pastes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    language: str = Query(None),
    created_after: str = Query(None),
    created_before: str = Query(None),
    _: str = Depends(verify_token)
):
    filters = []
    params = []

    filter_map = {
        "name LIKE ?": f"%{search}%" if search else None,
        "language = ?": language,
        "created_at >= ?": created_after,
        "created_at <= ?": created_before,
    }

    for condition, value in filter_map.items():
        if value is not None:
            filters.append(condition)
            params.append(value)

    where_clause = " AND ".join(filters) if filters else "1=1"

    conn = get_connection()

    total = conn.execute(f"SELECT COUNT(*) FROM pastes WHERE {where_clause}", params).fetchone()[0]

    offset = (page - 1) * limit
    rows = conn.execute(
        f"SELECT * FROM pastes WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()

    pastes = [PasteResponse(**dict(row)) for row in rows]

    return PasteListResponse(pastes=pastes, page=page, limit=limit, total=total)
