import os
import re
from collections import defaultdict

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox


# ── App-wide settings ──────────────────────────────────────────────────────────

_settings = QSettings("MyFileLab", "MyFileLab")


def get_setting(key: str, default=None):
    return _settings.value(key, default)


def set_setting(key: str, value):
    _settings.setValue(key, value)


def last_dir() -> str:
    return _settings.value("last_dir", "") or os.path.expanduser("~")


def set_last_dir(path: str):
    if path and os.path.exists(path):
        _settings.setValue("last_dir", os.path.dirname(path) if os.path.isfile(path) else path)


def recent_files(feature: str) -> list:
    files = _settings.value(f"recent/{feature}", [])
    return [f for f in (files or []) if os.path.exists(f)]


def add_recent_file(feature: str, path: str):
    files = recent_files(feature)
    if path in files:
        files.remove(path)
    files.insert(0, path)
    _settings.setValue(f"recent/{feature}", files[:10])


def window_geometry():
    return _settings.value("window/geometry")


def set_window_geometry(geo):
    _settings.setValue("window/geometry", geo)


# ── Page range parser (shared across merge, split, delete) ─────────────────────

def parse_page_range(raw: str, total_pages: int, zero_based: bool = True) -> list:
    """Parse a comma-separated page spec like '1-3, 5, 7-9' into a list of page indices.

    Args:
        raw: The raw string input (e.g. '1-3, 5').
        total_pages: Total number of pages in the document.
        zero_based: If True, returned indices are 0-based (for PdfReader).
                    If False, pages are 1-based (for display).

    Returns:
        List of int indices sorted ascending with duplicates removed.
    """
    if not raw.strip():
        return list(range(total_pages))
    indices = []
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            a_str, b_str = part.split("-", 1)
            a, b = int(a_str), int(b_str)
            if a < 1 or b > total_pages or a > b:
                raise ValueError(f"Range '{part}' is out of bounds (1–{total_pages}).")
            if zero_based:
                indices.extend(range(a - 1, b))
            else:
                indices.extend(range(a, b + 1))
        else:
            val = int(part)
            if val < 1 or val > total_pages:
                raise ValueError(f"Page {val} is out of bounds (1–{total_pages}).")
            if zero_based:
                indices.append(val - 1)
            else:
                indices.append(val)
    return sorted(set(indices))


def parse_page_range_groups(raw: str, total_pages: int) -> list:
    """Parse specs like '1-3, 5, 7-9' into separate groups: [[0,1,2], [4], [6,7,8]].

    Each comma-separated token becomes its own group (preserving its internal range
    as a contiguous list). This is used for the Split feature to create separate PDFs
    per token.
    """
    groups = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a_str, b_str = token.split("-", 1)
            start, end = int(a_str), int(b_str)
        else:
            start = end = int(token)
        if start < 1 or end > total_pages or start > end:
            raise ValueError(f"Range '{token}' is out of bounds (1–{total_pages}).")
        groups.append(list(range(start - 1, end)))
    return groups


# ── Safe filename ──────────────────────────────────────────────────────────────

def safe_filename(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip() or "video"


def readable_size(bytes_val: int) -> str:
    """Return a human-readable size string from bytes."""
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


# ── Password prompt for encrypted PDFs ─────────────────────────────────────────

def prompt_password(parent, filepath: str) -> str | None:
    """Show a dialog asking for the PDF password. Returns password or None."""
    from PySide6.QtWidgets import QInputDialog, QLineEdit
    text, ok = QInputDialog.getText(
        parent, "Password Required",
        f"The PDF is encrypted:\n{os.path.basename(filepath)}\n\nEnter password:",
        QLineEdit.EchoMode.Password
    )
    return text if ok and text else None


def open_pdf_reader(filepath: str, parent=None):
    """Open a PdfReader, prompting for password if needed. Returns PdfReader or raises."""
    from pypdf import PdfReader
    try:
        reader = PdfReader(filepath)
        if reader.is_encrypted:
            if parent is None:
                raise ValueError("PDF is encrypted and no parent widget for password prompt.")
            password = prompt_password(parent, filepath)
            if password is None:
                raise ValueError("Password required to open this PDF.")
            reader.decrypt(password)
            if reader.is_encrypted:
                raise ValueError("Incorrect password.")
        return reader
    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            raise
        raise


def open_fitz_doc(filepath: str, parent=None):
    """Open a fitz Document, prompting for password if needed."""
    import fitz
    try:
        return fitz.open(filepath)
    except Exception as e:
        msg = str(e).lower()
        if "password" in msg or "encrypted" in msg:
            if parent is None:
                raise ValueError("PDF is encrypted and no parent widget for password prompt.")
            password = prompt_password(parent, filepath)
            if password is None:
                raise ValueError("Password required to open this PDF.")
            try:
                return fitz.open(filepath, password=password)
            except Exception:
                raise ValueError("Incorrect password or unable to open PDF.")
        raise
