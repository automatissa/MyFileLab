# AutoPDF Pro

A fast, offline desktop app for PDF processing. No cloud, no subscriptions — everything runs locally.

Built with Python and PySide6.

---

## Features

| Feature | Description |
|---|---|
| **Merge PDFs** | Combine multiple PDFs into one. Drag & drop files into the list, reorder with ↑ ↓ buttons, and set optional page ranges per file (e.g. `1-3, 5`) |
| **Delete Pages** | Remove specific pages or ranges (e.g. `1, 3, 5-10`) from any PDF and save a new copy |
| **PDF to Word** | Convert PDF files into editable `.docx` documents |
| **MD to PDF** | Convert Markdown files (`.md`, `.markdown`) into formatted, styled PDF documents with support for tables, fenced code blocks, and headings |
| **PDF to MD** | Extract text from a PDF page-by-page and save it as a `.md` Markdown file |

---

## UI & UX

- Dark theme with a sidebar navigation and stacked content panels
- Animated loading dialog (braille spinner + progress bar) shown during every conversion
- All processing runs in a background thread — the UI stays responsive
- Drag & drop support for adding PDF files in the Merge view

---

## Installation

### Requirements

- Python 3.10+

### Setup

```bash
# Clone the repo
git clone https://github.com/automatissa/autopdf.git
cd autopdf

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
.venv\Scripts\python main.py
```

---

## Tech Stack

| Library | Role |
|---|---|
| `PySide6` | Desktop UI (Qt6) |
| `PyMuPDF` (`fitz`) | PDF rendering, text extraction, and MD→PDF story layout |
| `pdf2docx` | PDF → Word (`.docx`) conversion |
| `pypdf` | PDF merging and page deletion |
| `markdown` | Markdown parsing (tables, fenced code) for MD → PDF |
| `cryptography` | Encrypted PDF support (used internally by pypdf) |

---

## Project Structure

```
autopdf/
├── main.py                      # App entry point, layout, sidebar nav, theme
├── features/
│   ├── base_feature.py          # Shared base class — runs tasks in a background thread
│   ├── worker.py                # QThread worker that executes conversion functions
│   ├── processing_dialog.py     # Animated loading dialog (spinner + indeterminate bar)
│   ├── merge_feature.py         # Merge PDFs with drag & drop, reorder, page ranges
│   ├── delete_pages_feature.py  # Delete specific pages or ranges from a PDF
│   ├── pdf_to_word_feature.py   # PDF → .docx conversion
│   ├── md_to_pdf_feature.py     # Markdown → PDF with HTML styling via PyMuPDF Story
│   └── pdf_to_md_feature.py     # PDF text extraction → .md file
├── requirements.txt
└── icon_autopdf.ico
```

---

## License

GNU General Public License v3.0 — free to use, modify, and distribute under the same terms. See [LICENSE](LICENSE) for details.

---

Built by [@automatissa](https://github.com/automatissa) in collaboration with Gemini AI and Claude Code.
