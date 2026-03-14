# MyFileLab

Stop paying. Start owning.

A free, offline, open-source desktop app that replaces paid SaaS tools for PDF processing and video downloading. No cloud. No subscriptions. No file size limits. Everything runs on your machine.

Built with Python and PySide6.

---

## Why MyFileLab?

| SaaS tools charge you for | MyFileLab gives you for free |
|---|---|
| Merging PDFs | ✅ |
| Compressing PDFs | ✅ |
| Splitting PDFs | ✅ |
| PDF → Word | ✅ |
| Downloading videos from 10 platforms | ✅ |
| Extracting MP3 from any video URL | ✅ |
| Privacy (your files never leave your machine) | ✅ |

---

## Features

### PDF Tools

| Feature | Description |
|---|---|
| **Merge PDFs** | Combine multiple PDFs. Drag & drop, reorder, set per-file page ranges (e.g. `1-3, 5`) |
| **Delete Pages** | Remove pages or ranges (e.g. `1, 3, 5-10`) |
| **Compress PDF** | 3 presets — Light / Medium / Maximum. Shows before/after size and % saved |
| **Split PDF** | Split into individual pages or extract ranges (e.g. `1-3, 5, 7-9`) |
| **PDF → Word** | Convert to editable `.docx` |
| **MD → PDF** | Markdown to styled PDF — tables, code blocks, headings |
| **PDF → MD** | Extract PDF text as `.md` |

### Video & Audio Downloader

One feature, 10 platforms. Select platform → paste URL → pick quality → download.

| Platform | |
|---|---|
| YouTube | All resolutions up to 4K |
| Instagram | Posts, Reels, Stories |
| TikTok | |
| Twitter / X | |
| Facebook | |
| LinkedIn | |
| Twitch | VODs |
| Vimeo | |
| Dailymotion | |
| **Audio (MP3)** | 192kbps MP3 from any supported URL |

- Real-time progress bar
- Exact quality — formats pinned at fetch time
- ffmpeg bundled, no install needed

---

## Installation

**Requirements:** Python 3.10+

```bash
git clone https://github.com/automatissa/myfilelab.git
cd myfilelab

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
| `PyMuPDF` | PDF rendering, compression |
| `pypdf` | PDF merge, split, delete pages |
| `pdf2docx` | PDF → Word |
| `markdown` | MD → PDF parsing |
| `yt-dlp` | Video & audio downloading (1000+ sites) |
| `imageio-ffmpeg` | Bundled ffmpeg — no system install needed |
| `cryptography` | Encrypted PDF support |

---

## Project Structure

```
myfilelab/
├── main.py                         # Entry point, sidebar, theme
├── features/
│   ├── base_feature.py             # Base class — dialog helpers, task runner
│   ├── worker.py                   # Background thread worker
│   ├── processing_dialog.py        # Loading dialog
│   ├── merge_feature.py
│   ├── delete_pages_feature.py
│   ├── compress_pdf_feature.py
│   ├── split_pdf_feature.py
│   ├── pdf_to_word_feature.py
│   ├── md_to_pdf_feature.py
│   ├── pdf_to_md_feature.py
│   └── video_downloader_feature.py
├── requirements.txt
└── icon_autopdf.ico
```

---

## Built on the shoulders of giants

MyFileLab exists because these open source projects exist. Full respect.

| Project | What it does for us |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The engine behind the entire video & audio downloader — 1000+ sites, free forever |
| [FFmpeg](https://ffmpeg.org) | Merges video/audio streams, converts to MP3 — the backbone of media processing |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | Fast, powerful PDF rendering and compression |
| [pypdf](https://github.com/py-pdf/pypdf) | Pure Python PDF merge, split, and page manipulation |
| [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx) | PDF → Word conversion |
| [Python-Markdown](https://github.com/Python-Markdown/markdown) | Markdown parsing for MD → PDF |
| [PySide6 / Qt](https://www.qt.io) | The entire UI framework |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | Bundles ffmpeg as a Python package — no system install needed |

Without these projects, MyFileLab would be a blank window.
Go star their repos.

---

## License

GPL-3.0 — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

Built by [@automatissa](https://github.com/automatissa) with Gemini AI & Claude Code.
