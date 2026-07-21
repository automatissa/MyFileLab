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
| Image enhancement | ✅ |
| Batch image conversion | ✅ |
| Downloading videos from 1000+ platforms | ✅ |
| Extracting MP3 from any video URL | ✅ |
| Privacy (your files never leave your machine) | ✅ |

---

## Download

Go to the [Releases](https://github.com/automatissa/MyFileLab/releases) page and download for your OS.

### Windows
Download `MyFileLab-Windows.exe` → double-click to run. No install needed.

### macOS
1. Download `MyFileLab-Mac.zip`
2. Unzip it → drag `MyFileLab.app` to your Applications folder
3. **First launch only:** right-click the app → **Open** → click **Open Anyway**

> macOS blocks apps from unidentified developers by default. Right-click → Open bypasses this. You only need to do it once.

### Linux
1. Download `MyFileLab-Linux`
2. Make it executable and run:
```bash
chmod +x MyFileLab-Linux
./MyFileLab-Linux
```

---

## Features

### PDF Tools

| Feature | Description |
|---|---|
| **Merge PDFs** | Combine multiple PDFs. Drag & drop, reorder, set per-file page ranges (e.g. `1-3, 5`) |
| **Split PDF** | Split into individual pages or extract ranges (e.g. `1-3, 5, 7-9`) |
| **Delete Pages** | Remove pages or ranges (e.g. `1, 3, 5-10`) |
| **Compress PDF** | 3 presets — Light / Medium / Maximum. Shows before/after size and % saved |

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

### Metadata Editor

| Feature | Description |
|---|---|
| **View & Edit Metadata** | Read/write metadata for PDF, DOCX, XLSX, PPTX. Read EXIF for images |
| **Table layout** | 4-column view: checkbox, field name, current value, edit input |
| **Preserves unmodified data** | Only checked fields are written; everything else stays intact |

---

## Run from source

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

---

## Tech Stack

| Library | Role |
|---|---|
| `PySide6` | Desktop UI (Qt6) |
| `PyMuPDF` | PDF rendering and compression |
| `pypdf` | PDF merge, split, delete pages |
| `pdf2docx` | PDF → Word |
| `pdfplumber` | PDF → Excel (table extraction) |
| `openpyxl` | Write `.xlsx` files |
| `markdown` | Markdown → PDF parsing |
| `Pillow` | Image enhance and batch export |
| `lxml` | Office Open XML metadata read/write (docx/xlsx/pptx) |
| `yt-dlp` | Video & audio downloading (1000+ sites) |
| `imageio-ffmpeg` | Bundled FFmpeg — no system install needed |
| `cryptography` | Encrypted PDF support |

---

## Built on the shoulders of giants

| Project | What it does for us |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The engine behind the entire media downloader |
| [FFmpeg](https://ffmpeg.org) | Merges video/audio streams, converts to MP3 |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | Fast PDF rendering and compression |
| [pypdf](https://github.com/py-pdf/pypdf) | Pure Python PDF manipulation |
| [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx) | PDF → Word conversion |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | PDF table extraction |
| [Pillow](https://github.com/python-pillow/Pillow) | Image processing |
| [Python-Markdown](https://github.com/Python-Markdown/markdown) | Markdown parsing |
| [PySide6 / Qt](https://www.qt.io) | The entire UI framework |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | Bundled FFmpeg as a Python package |

---

## License

AGPL-3.0 — free to use, modify, and distribute. Any use, including over a network, requires sharing modifications. See [LICENSE](LICENSE).

---

Built by [Issa Diouf](https://www.linkedin.com/in/issadiouf/) · [GitHub](https://github.com/automatissa/MyFileLab)
