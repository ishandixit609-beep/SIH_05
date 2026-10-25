from __future__ import annotations

import math
from typing import Any, Optional


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def point_in_polygon(lat: float, lon: float, polygon: list[list[float]]) -> bool:
    """Ray casting point-in-polygon test."""
    inside = False
    n = len(polygon)
    for i in range(n):
        j = (i - 1) % n
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]
        intersect = ((yi > lon) != (yj > lon)) and (
            lat < (xj - xi) * (lon - yi) / (yj - yi) + xi
        )
        if intersect:
            inside = not inside
    return inside


def compute_photo_statuses(
    campus_polygon: list[list[float]],
    photos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute status ('inside_campus' | 'far_from_campus' | 'no_location_data') and km distance."""
    results: list[dict[str, Any]] = []

    for p in photos:
        p_copy = dict(p)
        lat = p_copy.get("lat")
        lon = p_copy.get("lon")

        if lat is None or lon is None:
            p_copy["status"] = "no_location_data"
            p_copy["km"] = None
        elif point_in_polygon(lat, lon, campus_polygon):
            p_copy["status"] = "inside_campus"
            p_copy["km"] = 0.0
        else:
            dists = [haversine_km(lat, lon, v[0], v[1]) for v in campus_polygon]
            min_dist = min(dists) if dists else 0.0
            p_copy["status"] = "far_from_campus"
            p_copy["km"] = round(float(min_dist), 1)

        results.append(p_copy)

    return results
