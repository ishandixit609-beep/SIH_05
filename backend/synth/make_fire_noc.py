from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DEFAULT_NUMBER = "SYN/FIRE/PMC/2026/4471"
DEFAULT_ISSUE = "01-10-2026"
DEFAULT_VALID = "30-09-2027"
DEFAULT_FLOORS = 5
DEFAULT_AUTHORITY = "State Fire Service (synthetic)"
DEFAULT_PREMISES = "Plot 42, Sector 10, Wakad, Pune, Maharashtra - 411057"


def generate_fire_noc(
    out_path: Path,
    number: str = DEFAULT_NUMBER,
    issue_date: str = DEFAULT_ISSUE,
    valid_till: str = DEFAULT_VALID,
    max_floors: int = DEFAULT_FLOORS,
    premises: str = DEFAULT_PREMISES,
    authority: str = DEFAULT_AUTHORITY,
    expired: bool = False,
    tampered: bool = False,
    renewed: bool = False,
    producer: Optional[str] = None,
    creation_date: Optional[str] = None,
    mod_date: Optional[str] = None,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if expired:
        valid_till = "10-01-2027"
    elif renewed:
        number = "SYN/FIRE/PMC/2027/5501"
        valid_till = "31-12-2028"

    if tampered:
        number = "SYN/FIRE/PMC/2026/9999"  # Not in simulated registry
        producer = producer or "Adobe Photoshop 24.1 (synthetic edit)"
        creation_date = creation_date or "D:20261001100000+05'30'"
        mod_date = mod_date or "D:20261003153000+05'30'"  # > 48h later
    else:
        producer = producer or "ReportLab PDF Library (synthetic)"
        creation_date = creation_date or "D:20261001100000+05'30'"
        mod_date = mod_date or "D:20261001100500+05'30'"

    # 1. Render PDF layout with ReportLab
    c = canvas.Canvas(str(out_path), pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, height - 72, "Fire Safety Certificate (NOC)")

    c.setFont("Helvetica", 10)
    c.drawString(72, height - 90, "Government of Maharashtra · State Fire Services Directorate")

    c.line(72, height - 98, width - 72, height - 98)

    y = height - 130
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, f"Certificate Number: {number}")

    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(72, y, f"Issued on: {issue_date}")

    y -= 25
    c.drawString(72, y, f"Valid till: {valid_till}")

    y -= 25
    c.drawString(72, y, f"Maximum floors: {max_floors}")

    y -= 25
    c.drawString(72, y, f"Issuing authority: {authority}")

    y -= 25
    c.drawString(72, y, f"Premises: {premises}")

    y -= 50
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(72, y, "SYNTHETIC DOCUMENT - not a real certificate")
    c.drawString(72, y - 15, "Generated for SATYAPAN / ISHAN AICTE Scrutiny Demonstration")

    c.save()

    # 2. Set metadata with PyMuPDF
    doc = fitz.open(str(out_path))
    meta = doc.metadata
    meta["title"] = "Fire NOC (synthetic)"
    meta["author"] = authority
    meta["producer"] = producer
    meta["creationDate"] = creation_date
    meta["modDate"] = mod_date
    doc.set_metadata(meta)
    doc.save(str(out_path), incremental=True, encryption=0)
    doc.close()

    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Fire NOC PDF with metadata and evidence boxes")
    parser.add_argument("--out", type=str, default="data/samples/fire_noc_demo.pdf")
    parser.add_argument("--expired", action="store_true", help="Generate expired NOC (valid-till before 12-01-2027)")
    parser.add_argument("--tampered", action="store_true", help="Generate tampered NOC (unregistered number, mod date >> creation)")
    parser.add_argument("--renewed", action="store_true", help="Generate renewed NOC (valid till 31-12-2028, covers all semesters)")
    args = parser.parse_args()

    out_file = Path(args.out)
    generate_fire_noc(out_file, expired=args.expired, tampered=args.tampered, renewed=args.renewed)
    print(f"Generated Fire NOC: {out_file} (expired={args.expired}, tampered={args.tampered}, renewed={args.renewed})")


if __name__ == "__main__":
    main()
