from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db, get_db, ensure_demo_sample
from app.engines.geo import compute_photo_statuses, haversine_km, point_in_polygon
from app.extract.llm_fire_noc import LLMFireNocExtractor, init_llm_cache_table

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_phase6():
    init_db()
    client.post("/api/_reset")
    yield


def test_geo_haversine_and_point_in_polygon():
    polygon = [
        [18.59, 73.736],
        [18.59, 73.744],
        [18.596, 73.744],
        [18.596, 73.736],
    ]

    # Inside point
    assert point_in_polygon(18.593, 73.74, polygon) is True

    # Far outside point
    assert point_in_polygon(18.935, 73.74, polygon) is False

    # Haversine distance
    dist = haversine_km(18.596, 73.74, 18.935, 73.74)
    assert 37.0 < dist < 39.0


def test_compute_photo_statuses_and_endpoint():
    polygon = [
        [18.59, 73.736],
        [18.59, 73.744],
        [18.596, 73.744],
        [18.596, 73.736],
    ]
    test_photos = [
        {"photo": 1, "lat": None, "lon": None},
        {"photo": 2, "lat": 18.593, "lon": 73.74},
        {"photo": 3, "lat": 18.935, "lon": 73.74},
    ]

    computed = compute_photo_statuses(polygon, test_photos)
    assert computed[0]["status"] == "no_location_data"
    assert computed[0]["km"] is None

    assert computed[1]["status"] == "inside_campus"
    assert computed[1]["km"] == 0.0

    assert computed[2]["status"] == "far_from_campus"
    assert computed[2]["km"] == 37.7

    # Test via API
    res = client.get("/api/applications/APP-0001/photos")
    assert res.status_code == 200
    photos_data = res.json()["photos"]
    assert len(photos_data) == 6
    # Photos 1 & 2 have no GPS
    assert photos_data[0]["status"] == "no_location_data"
    assert photos_data[1]["status"] == "no_location_data"
    # Photos 3 & 4 inside
    assert photos_data[2]["status"] == "inside_campus"
    assert photos_data[3]["status"] == "inside_campus"
    # Photos 5 & 6 far
    assert photos_data[4]["status"] == "far_from_campus"
    assert photos_data[5]["status"] == "far_from_campus"


def test_llm_extractor_fallback_and_cache(tmp_path: Path):
    sample_path = ensure_demo_sample()
    import hashlib
    doc_sha = hashlib.sha256(sample_path.read_bytes()).hexdigest()
    with get_db() as conn:
        init_llm_cache_table(conn)
        conn.execute("DELETE FROM llm_cache WHERE sha256 = ?", (doc_sha,))
        conn.commit()

    extractor = LLMFireNocExtractor()

    # 1. Fallback to regex when no API key is set -> ai_read=False
    fields_fallback = extractor.extract(sample_path)
    assert len(fields_fallback) >= 3
    assert all(f["ai_read"] is False for f in fields_fallback)

    # 2. Cached response from DB -> ai_read=True
    cached_data = {
        "number": "SYN/FIRE/PMC/2026/4471",
        "valid_till": "30-09-2027",
        "max_floors": 5,
        "issue_date": "01-10-2026",
        "premises": "Plot 42, Sector 10, Wakad, Pune, Maharashtra - 411057",
        "agency": "State Fire Service (synthetic)",
    }
    with get_db() as conn:
        init_llm_cache_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO llm_cache (sha256, response, created_at) VALUES (?, ?, 1000.0)",
            (doc_sha, json.dumps(cached_data)),
        )
        conn.commit()

    fields_cached = extractor.extract(sample_path)
    assert len(fields_cached) >= 3
    assert all(f["ai_read"] is True for f in fields_cached)
    num_f = next(f for f in fields_cached if f["key"] == "fire_noc.number")
    assert num_f["value"] == "SYN/FIRE/PMC/2026/4471"
    assert num_f["ai_read"] is True
