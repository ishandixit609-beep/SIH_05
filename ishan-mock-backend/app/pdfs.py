"""Generates the 9 synthetic PDFs (ReportLab) and evidence boxes (PDF points, origin top-left)."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

PAGE_H = A4[1]
FONT, SIZE = "Helvetica", 12
FOOTER = "SYNTHETIC DOCUMENT - generated for the ISHAN demo - not a real certificate"
DOCS = {"D-01": ("Trust affidavit and undertakings", 1), "D-02": ("Land record (7/12 extract)", 3),
        "D-03": ("Architect-certified area statement", 8), "D-04": ("Fire NOC", 1),
        "D-05": ("University affiliation letter", 1), "D-06": ("Accreditation certificate (old format)", 1),
        "D-07": ("Faculty and library list", 4), "D-08": ("Financial soundness (FDR)", 1),
        "D-09": ("Building completion certificate", 1)}
TRUST_A, TRUST_B = "Shri Vidya Shikshan Prasarak Mandal", "Shri Vidyadhar Shikshan Prasarak Mandal"
# (doc, page, baseline_y, line text, phrase to box or None, findings it supports)
LINES = [("D-01", 1, 770, "Trust affidavit", None, []),
         ("D-01", 1, 710, f"Trust name: {TRUST_A}", TRUST_A, ["F-011", "F-012"]),
         ("D-02", 3, 770, "Land record (7/12 extract)", None, []),
         ("D-02", 3, 710, f"Owner: {TRUST_B}", TRUST_B, ["F-011", "F-013"]),
         ("D-03", 8, 770, "Area statement", None, []),
         ("D-03", 8, 740, "Sanctioned plan area: 2,400 sq m", None, []),
         ("D-03", 8, 710, "Built-up area: 1,800 sq m", "Built-up area: 1,800 sq m", ["F-014"]),
         ("D-03", 8, 680, "Carpet area: 1,720 sq m", "Carpet area: 1,720 sq m", ["F-015"]),
         ("D-03", 8, 650, "Intake applied: 600", None, []),
         ("D-04", 1, 770, "Fire NOC (State Fire Services)", None, []),
         ("D-04", 1, 710, "Valid till 30-09-2027", "Valid till 30-09-2027", ["F-016"]),
         ("D-05", 1, 770, "University affiliation letter", None, []),
         ("D-06", 1, 770, "Accreditation certificate (old format)", None, []),
         ("D-07", 4, 770, "Faculty and library list", None, []),
         ("D-07", 4, 710, "Full-time faculty: 83", "Full-time faculty: 83", ["F-018"]),
         ("D-08", 1, 770, "Financial soundness: fixed deposit receipt", None, []),
         ("D-09", 1, 770, "Building completion certificate", None, [])]

def _box(line, phrase, baseline):
    x0 = 72 + stringWidth(line[:line.index(phrase)], FONT, SIZE)
    x1 = x0 + stringWidth(phrase, FONT, SIZE)
    top = PAGE_H - baseline
    return [round(x0, 1), round(top - 0.9 * SIZE, 1), round(x1, 1), round(top + 0.25 * SIZE, 1)]

def build(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for did, (title, pages) in DOCS.items():
        c = canvas.Canvas(str(out_dir / f"{did}.pdf"), pagesize=A4)
        for pg in range(1, pages + 1):
            c.setFont(FONT, SIZE)
            lines = [l for l in LINES if l[0] == did and l[1] == pg]
            if not lines: c.drawString(72, 770, f"{title} - page {pg}")
            for _, _, y, text, _, _ in lines: c.drawString(72, y, text)
            c.setFont(FONT, 8); c.drawString(72, 60, FOOTER)
            c.showPage()
        c.save()
    boxes = {d: [] for d in DOCS}
    for d, p, y, text, phrase, fins in LINES:
        if phrase: boxes[d].append({"page": p, "box": _box(text, phrase, y), "text": phrase, "findings": fins})
    return boxes
