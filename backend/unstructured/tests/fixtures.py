"""Build tiny synthetic .xlsx workbooks for tests (standard library; no client data)."""
import zipfile
from pathlib import Path
from typing import Dict, List
from xml.sax.saxutils import escape


def _col(i: int) -> str:
    name = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        name = chr(65 + r) + name
    return name


def make_xlsx(path: Path, sheets: Dict[str, List[List[str]]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rel_ns = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    with zipfile.ZipFile(path, "w") as z:
        sheet_tags, rels = [], []
        for n, (name, rows) in enumerate(sheets.items(), start=1):
            sheet_tags.append(f'<sheet name="{escape(name)}" sheetId="{n}" r:id="rId{n}"/>')
            rels.append(f'<Relationship Id="rId{n}" Target="worksheets/sheet{n}.xml" '
                        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>')
            xml_rows = []
            for r, row in enumerate(rows, start=1):
                cells = "".join(f'<c r="{_col(c)}{r}" t="inlineStr"><is><t>{escape(v)}</t></is></c>'
                                for c, v in enumerate(row) if v)
                xml_rows.append(f'<row r="{r}">{cells}</row>')
            z.writestr(f"xl/worksheets/sheet{n}.xml", f'<worksheet {ns}><sheetData>{"".join(xml_rows)}</sheetData></worksheet>')
        z.writestr("xl/workbook.xml", f'<workbook {ns} {rel_ns}><sheets>{"".join(sheet_tags)}</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(rels) + "</Relationships>")
    return path


GUIDE_ROWS = [
    ["TEST COURIER — RESOLUTION GUIDE (internal)"],
    ["Owner: Test Owner · v2, updated 2 Mar 2026"],
    [],
    ["Complaint type", "Check first", "Resolution", "Limit / approval"],
    ["Late delivery", "Delivered vs promised date", "Under 2 days: apology only", "Agent"],
    ["COD overcharge", "Collected vs cod_amount", "Refund the difference only", "Agent"],
    ["Corporate account (TEST-*)", "Complaints this month", "Escalate", "Manager"],
    [],
    ["Notes"],
    ["• One complaint = one case."],
]
