import re


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

