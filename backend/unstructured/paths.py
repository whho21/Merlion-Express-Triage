"""Where the package lives, and how A writes source references.

Team plan v0.5 puts the package at data/team2_merlion_express_package/; some members unzipped straight into data/.
Both work: the default is whichever exists. --data always wins. The client's case-log workbook (Q01) goes in the
package's tabular/ folder, git-ignored like the rest.
"""
from __future__ import annotations

from pathlib import Path

PACKAGE_DIRS = (Path("data") / "team2_merlion_express_package", Path("data"))


def default_data_dir() -> Path:
    for candidate in PACKAGE_DIRS:
        if (candidate / "docs" / "complaint_emails").is_dir() or (candidate / "images").is_dir():
            return candidate
    return PACKAGE_DIRS[-1]


def source_ref(path: Path, data_dir: Path) -> str:
    """Repo-relative path when the file is under the working directory, else data/<path inside the package>."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return "data/" + path.relative_to(data_dir).as_posix()
