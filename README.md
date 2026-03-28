# MyFileLab

Stop paying. Start owning.

A free, offline, open-source desktop app that replaces paid SaaS tools for PDF processing, image editing, and media downloading. No cloud. No subscriptions. No file size limits. Everything runs on your machine.

Built with Python and PySide6.

---

## Why MyFileLab?

| SaaS tools charge you for | MyFileLab gives you for free |
|---|---|
| Merging PDFs | ✅ |
| Compressing PDFs | ✅ |
| Splitting PDFs | ✅ |
| PDF → Word / Excel | ✅ |
| OCR on scanned PDFs | ✅ |
| Image enhancement | ✅ |
| Batch image conversion | ✅ |
| Downloading videos from 1000+ platforms | ✅ |
| Extracting MP3 from any video URL | ✅ |
| Privacy (your files never leave your machine) | ✅ |

---

## Features

### PDF Tools

| Feature | Description |
|---|---|
| **Merge PDFs** | Combine multiple PDFs. Drag & drop, reorder, set per-file page ranges (e.g. `1-3, 5`) |
| **Split PDF** | Split into individual pages or extract ranges (e.g. `1-3, 5, 7-9`) |
| **Delete Pages** | Remove pages or ranges (e.g. `1, 3, 5-10`) |
| **Compress PDF** | 3 presets — Light / Medium / Maximum. Shows before/after size and % saved |
| **OCR** | Extract text from scanned PDFs — output as `.txt` or searchable PDF |

### Converter

| Feature | Description |
|---|---|
| **PDF → Word** | Convert to editable `.docx` |
| **PDF → Excel** | Table extraction with plain-text fallback |
| **Images → PDF** | Combine JPG, PNG and other images into a single PDF |
| **Markdown → PDF** | Styled PDF with tables, code blocks and headings |

### Images

| Feature | Description |
|---|---|
| **Enhance** | Adjust brightness, contrast, sharpness and colour with real-time preview |
| **Batch Export** | Convert multiple images to JPEG, PNG, WebP or BMP with quality control |

### Media Downloader

One tool, 1000+ platforms.

| Platform | Notes |
|---|---|
| YouTube | All resolutions up to 4K |
| Instagram | Posts, Reels, Stories |
| TikTok | |
| Twitter / X | |
| Facebook | |
| Vimeo | |
| Twitch | VODs |
| **+ 1000 more** | Powered by yt-dlp |
| **Audio (MP3)** | 192 kbps MP3 from any supported URL |

- Real-time progress bar per stream
- Exact quality selection — formats pinned at fetch time
- FFmpeg bundled, no install needed

---

## Installation

### Download (recommended)

Grab the latest release for your OS from the [Releases](https://github.com/automatissa/MyFileLab/releases) page. No install required — single executable.

> **OCR requires Tesseract.** The release builds bundle Tesseract automatically.
> For dev/source builds, install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).

### Run from source

**Requirements:** Python 3.10+

```bash
git clone https://github.com/automatissa/MyFileLab.git
cd MyFileLab

python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
python main.py
```

### Build a local .exe

```bash
.venv/Scripts/python.exe -m PyInstaller MyFileLab.spec --clean
# Output: dist/MyFileLab.exe
```

---

## Tech Stack

| Library | Role |
|---|---|
| `PySide6` | Desktop UI (Qt6) |
| `PyMuPDF` | PDF rendering, compression, OCR page rendering |
| `pypdf` | PDF merge, split, delete pages |
| `pdf2docx` | PDF → Word |
| `pdfplumber` | PDF → Excel (table extraction) |
| `openpyxl` | Write `.xlsx` files |
| `markdown` | Markdown → PDF parsing |
| `Pillow` | Image enhance and batch export |
| `Tesseract` | OCR engine (bundled in release builds) |
| `yt-dlp` | Video & audio downloading (1000+ sites) |
| `imageio-ffmpeg` | Bundled FFmpeg — no system install needed |
| `cryptography` | Encrypted PDF support |

---

## Project Structure

```
MyFileLab/
├── main.py                          # Entry point, sidebar, theme
├── features/
│   ├── base_feature.py              # BaseFeature, AppCard, ConversionWorker
│   ├── pdf_tools_feature.py         # Merge, Split, Delete, Compress, OCR
│   ├── pdf_export_feature.py        # PDF→Word, PDF→Excel, Images→PDF, MD→PDF
│   ├── image_tools_feature.py       # Enhance, Batch Export
│   └── video_downloader_feature.py  # Media Downloader
├── .github/workflows/build.yml      # CI — builds Windows / Mac / Linux .exe
├── requirements.txt
└── icon_autopdf.ico
```

---

## Built on the shoulders of giants

MyFileLab exists because these open source projects exist.

| Project | What it does for us |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The engine behind the entire media downloader — 1000+ sites |
| [FFmpeg](https://ffmpeg.org) | Merges video/audio streams, converts to MP3 |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | The OCR engine |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | Fast PDF rendering and compression |
| [pypdf](https://github.com/py-pdf/pypdf) | Pure Python PDF merge, split, page manipulation |
| [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx) | PDF → Word conversion |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | PDF table extraction |
| [Pillow](https://github.com/python-pillow/Pillow) | Image processing |
| [Python-Markdown](https://github.com/Python-Markdown/markdown) | Markdown parsing |
| [PySide6 / Qt](https://www.qt.io) | The entire UI framework |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | Bundled FFmpeg as a Python package |

Without these projects, MyFileLab would be a blank window.
Go star their repos.

---

## License

GPL-3.0 — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

Built by [Issa Diouf](https://www.linkedin.com/in/issadiouf/) · [GitHub](https://github.com/automatissa/MyFileLab)
