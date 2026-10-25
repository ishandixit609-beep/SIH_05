from __future__ import annotations

import os
from typing import Any, Optional, TypedDict


class RegistryRecord(TypedDict):
    number: str
    agency: str
    valid_till: str
    max_floors: int
    premises: str


REGISTRY_DATABASE: dict[str, RegistryRecord] = {
    "SYN/FIRE/PMC/2026/4471": {
        "number": "SYN/FIRE/PMC/2026/4471",
        "agency": "State Fire Service (synthetic)",
        "valid_till": "30-09-2027",
        "max_floors": 5,
        "premises": "Pune - 411057",
    },
    "SYN/FIRE/PMC/2027/5501": {
        "number": "SYN/FIRE/PMC/2027/5501",
        "agency": "State Fire Service (synthetic)",
        "valid_till": "31-12-2028",
        "max_floors": 5,
        "premises": "Pune - 411057",
    },
}


def lookup_fire_noc(
    number: str,
    valid_till: Optional[str] = None,
    max_floors: Optional[int] = None,
) -> dict[str, Any]:
    """Simulated issuer registry lookup."""
    if os.getenv("REGISTRY_DOWN", "").lower() in ("true", "1", "yes"):
        return {"status": "source_down", "record": None, "reason": "source unavailable"}

    cleaned_number = (number or "").strip()
    record = REGISTRY_DATABASE.get(cleaned_number)
    if not record:
        return {"status": "not_found", "record": None, "reason": "Certificate number not found in issuer registry"}

    # Check if dates and floors agree
    date_agrees = valid_till is None or record["valid_till"] == valid_till
    floors_agree = max_floors is None or record["max_floors"] == max_floors

    if date_agrees and floors_agree:
        return {"status": "agrees", "record": record, "reason": "Record agrees"}
    return {"status": "mismatch", "record": record, "reason": "Record fields do not agree with registry entry"}
