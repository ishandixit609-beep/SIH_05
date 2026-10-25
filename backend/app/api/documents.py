from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.db import get_db, ensure_demo_sample
from app.fixtures_layer import get_fixture_copy, FIXTURES_DIR
from app.checks.fire_noc import run_fire_noc_checks

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{doc_id}/boxes")
async def get_document_boxes(doc_id: str):
    base_boxes = get_fixture_copy("boxes")

    if doc_id == "D-04":
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fields FROM scrutiny_result WHERE app_id = 'APP-0001'")
            row = cursor.fetchone()
            if row:
                fields = json.loads(row["fields"])
            else:
                sample_path = ensure_demo_sample()
                res = run_fire_noc_checks(sample_path)
                fields = res["fields"]

        computed_boxes = []
        for f in fields:
            box = f.get("box", [0, 0, 0, 0])
            if any(x > 0 for x in box):
                computed_boxes.append({
                    "field": f["key"],
                    "text": f"{f['key'].split('.')[-1]}: {f['value']}",
                    "box": box,
                })

        base_boxes["D-04"] = {"1": computed_boxes}

    return base_boxes


@router.get("/{doc_id}/file")
@router.head("/{doc_id}/file")
async def get_document_file(doc_id: str):
    if doc_id == "D-04":
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM document WHERE id = 'D-04'")
            row = cursor.fetchone()
            if row and Path(row["path"]).exists():
                return FileResponse(row["path"], media_type="application/pdf")

    pdf_path = FIXTURES_DIR / "pdfs" / f"{doc_id}.pdf"
    if pdf_path.exists():
        return FileResponse(str(pdf_path), media_type="application/pdf")

    # Fallback to demo sample
    sample_path = ensure_demo_sample()
    if sample_path.exists():
        return FileResponse(str(sample_path), media_type="application/pdf")

    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
