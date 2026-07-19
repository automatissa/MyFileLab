# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Commands

```bash
# Dev
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
playwright install chromium   # one-time ~180 MB download for Markdown→PDF
python main.py

# Build (single-file exe)
pyinstaller MyFileLab.spec
```

Tests use `pytest`. Run with `python -m pytest tests\ -v`. No linter is configured.

## Architecture

**Feature plugin pattern** — `main.py` holds a `FEATURES` list. Each entry is a `BaseFeature` subclass. Adding a new feature means creating `features/your_feature.py`, subclassing `BaseFeature`, setting `NAV_NAME`, and appending the class to `FEATURES`. The sidebar nav and stack are built automatically at startup.

**`BaseFeature`** (`features/base_feature.py`) is the root every feature inherits from. Key methods to reuse:
- `run_with_dialog(fn, success_msg)` — runs `fn` in a `QThread`, shows the spinner dialog, then a success/error `QMessageBox`. Use this for every blocking operation.
- `primary_button(label, on_click)` — standard cyan action button.
- File/folder dialog helpers: `open_file_dialog`, `open_files_dialog`, `folder_dialog`, `save_dialog`.

**`AppCard`** — pass `on_click=None` to render it as a "Coming Soon" greyed-out card with no hover behaviour.

**Two PDF libraries coexist intentionally:**
- `pypdf` — merge, split, delete pages (pure Python, page-level manipulation)
- `PyMuPDF` (`fitz`) — compress, render, and the Markdown→PDF `fitz.Story` pipeline

**Asset resolution** — `_resource(relative)` in `main.py` resolves paths correctly in both dev and PyInstaller frozen builds via `sys._MEIPASS`. Use this for any bundled file (icons, binaries). The icon must be listed in `MyFileLab.spec` under `datas` to be included in the exe.

**Media downloader workers** — two-phase: `_VideoFetchWorker` calls yt-dlp with `skip_download=True` to enumerate quality options, then `_VideoDownloadWorker` does the actual download. FFmpeg is sourced from `imageio_ffmpeg.get_ffmpeg_exe()` — no system FFmpeg required.

**Metadata Editor** (`features/metadata_feature.py`) — single-table layout with 4 columns per row:
- Checkbox | Field Name | Current Value (read-only) | Edit Value (editable input)
- Only checked fields are written on Apply; unchecked fields are left untouched.
- Formats: PDF (pypdf read/write), OOXML (docx/xlsx/pptx via `lxml` + zipfile), Images (Pillow EXIF read-only)
- PDF writing preserves all unmodified metadata keys by reading originals first, then merging.
- OOXML writing is surgical: opens the ZIP, only modifies targeted elements in `docProps/core.xml`/`docProps/app.xml`, leaves everything else intact.
- `_FIELD_DEFS` defines the display order; `_CORE_MAP_DICT`/`_APP_MAP_DICT`/`_PDF_KEY_MAP` map field keys to format-specific paths.
- `_EditRow` is a custom `QFrame` widget with all 4 columns: checkbox toggles edit input between editable (cyan border) and disabled (grey).
- Image metadata writing is not yet implemented; the Apply button shows "coming soon" for image files.

**Shared utilities** (`features/utils.py`):
- Settings: `get_setting`/`set_setting`/`last_dir`/`recent_files`/`window_geometry` (QSettings helpers)
- `parse_page_range` — parses comma-separated page specs (`1-3, 5, 7-9`) into 0-based index lists
- `parse_page_range_groups` — same but returns separate groups for split feature
- `safe_filename` / `readable_size` — string formatting helpers
- `prompt_password` / `open_pdf_reader` / `open_fitz_doc` — encrypted PDF handling
