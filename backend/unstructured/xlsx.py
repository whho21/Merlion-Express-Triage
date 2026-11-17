"""Read .xlsx cell text with the standard library only (an .xlsx file is a zip of XML parts).

Enough for the client's workbook: shared strings, inline strings and plain values, placed by their cell
reference (C5 -> column 3) so sparse rows keep their columns. No formulas are evaluated: the cached value is read.
"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")

Row = Tuple[int, List[str]]  # (Excel row number, cell texts by column)


class XlsxError(Exception):
    pass


def _col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _text(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.iter(M + "t"))


def read_workbook(path: Path) -> Dict[str, List[Row]]:
    """Return {sheet name: [(row number, [cell text, ...]), ...]} in workbook order."""
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            shared = []
            if "xl/sharedStrings.xml" in names:
                shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si")]
            rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
            sheets: Dict[str, List[Row]] = {}
            for sheet in ET.fromstring(z.read("xl/workbook.xml")).find(M + "sheets"):
                target = rels[sheet.get(R + "id")].lstrip("/")
                part = target if target.startswith("xl/") else "xl/" + target
                rows: List[Row] = []
                for row in ET.fromstring(z.read(part)).iter(M + "row"):
                    cells: Dict[int, str] = {}
                    for i, c in enumerate(row.findall(M + "c")):
                        ref = CELL_RE.match(c.get("r") or "")
                        col = _col_index(ref.group(1)) if ref else i
                        kind, value = c.get("t"), c.find(M + "v")
                        if kind == "s" and value is not None:
                            cells[col] = shared[int(value.text)]
                        elif kind == "inlineStr":
                            cells[col] = _text(c)
                        else:
                            cells[col] = value.text if value is not None and value.text else ""
                    width = max(cells) + 1 if cells else 0
                    rows.append((int(row.get("r") or len(rows) + 1), [cells.get(i, "") for i in range(width)]))
                sheets[sheet.get("name")] = rows
            return sheets
    except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError, IndexError, TypeError) as exc:
        raise XlsxError(f"{type(exc).__name__}: {exc}") from exc
