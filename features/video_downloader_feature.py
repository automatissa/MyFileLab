import re
from collections import defaultdict

import imageio_ffmpeg
import yt_dlp
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QFrame, QProgressBar, QGridLayout
)

from .base_feature import BaseFeature

# ── Theme ──────────────────────────────────────────────────────────────────────
_BG_CARD  = "#2a2a2c"
_BG_INPUT = "#1C1C1E"
_BORDER   = "#3a3a3a"
_ACCENT   = "#00f6ff"
_MUTED    = "#888"

_CARD_OFF  = "QFrame { background:#2a2a2c; border-radius:14px; border:1px solid #383838; }"
_CARD_OVER = "QFrame { background:#2e2e30; border-radius:14px; border:1px solid #444; }"
_CARD_ON   = "QFrame { background:rgba(0,246,255,0.07); border-radius:14px; border:2px solid rgba(0,246,255,0.4); }"

_COLOR_VIDEO = "#007AFF"
_COLOR_AUDIO = "#1DB954"


# ── Selectable format card ─────────────────────────────────────────────────────

class _SelectCard(QFrame):
    def __init__(self, letter: str, color: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self._selected = False
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(_CARD_OFF)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        icon = QLabel(letter)
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"background:{color}; border-radius:9px; color:white; "
            f"font-size:15px; font-weight:bold; border:none;"
        )
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignLeft)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            "color:white; font-size:14px; font-weight:bold; "
            "background:transparent; border:none;"
        )
        layout.addWidget(self._title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            f"color:{_MUTED}; font-size:11px; background:transparent; border:none;"
        )
        layout.addWidget(desc_lbl)

    @property
    def selected(self) -> bool:
        return self._selected

    def mousePressEvent(self, e):
        self._selected = not self._selected
        self._refresh()
        super().mousePressEvent(e)

    def enterEvent(self, e):
        if not self._selected:
            self.setStyleSheet(_CARD_OVER)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._refresh()
        super().leaveEvent(e)

    def _refresh(self):
        if self._selected:
            self.setStyleSheet(_CARD_ON)
            self._title_lbl.setStyleSheet(
                "color:#00f6ff; font-size:14px; font-weight:bold; "
                "background:transparent; border:none;"
            )
        else:
            self.setStyleSheet(_CARD_OFF)
            self._title_lbl.setStyleSheet(
                "color:white; font-size:14px; font-weight:bold; "
                "background:transparent; border:none;"
            )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_filename(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip() or "video"


def _height_label(h: int) -> str:
    labels = {2160: "4K · 2160p", 1440: "2K · 1440p", 1080: "Full HD · 1080p",
              720: "HD · 720p", 480: "480p", 360: "360p", 240: "240p", 144: "144p"}
    return labels.get(h, f"{h}p")


# ── Background workers ─────────────────────────────────────────────────────────

class _VideoFetchWorker(QThread):
    finished = Signal(list, str)
    error    = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self._url, download=False)

            title   = info.get("title") or "video"
            formats = info.get("formats", [])

            audio_only_fmts = [
                f for f in formats
                if f.get("acodec") not in (None, "none")
                and f.get("vcodec") in (None, "none")
            ]
            best_audio = None
            if audio_only_fmts:
                m4a  = [f for f in audio_only_fmts
                        if f.get("ext") == "m4a" or "mp4a" in (f.get("acodec") or "")]
                pool = m4a if m4a else audio_only_fmts
                best_audio = max(pool, key=lambda f: f.get("abr") or f.get("tbr") or 0)

            by_height: dict = defaultdict(list)
            for f in formats:
                if f.get("vcodec") in (None, "none"):
                    continue
                h = f.get("height")
                if h and h > 0:
                    by_height[h].append(f)

            choices = []
            if by_height:
                for h in sorted(by_height.keys(), reverse=True):
                    best_v = max(by_height[h],
                                 key=lambda f: f.get("vbr") or f.get("tbr") or 0)
                    vid_id = best_v["format_id"]
                    has_audio = best_v.get("acodec") not in (None, "none")
                    if best_audio:
                        fmt_id = f"{vid_id}+{best_audio['format_id']}"
                    elif has_audio:
                        # stream already contains audio (e.g. Twitter/X)
                        fmt_id = vid_id
                    else:
                        # no separate audio stream and video has no audio — let yt-dlp pick
                        fmt_id = f"{vid_id}+bestaudio/best"
                    choices.append((_height_label(h), fmt_id))
            else:
                video_fmts = [f for f in formats if f.get("vcodec") not in (None, "none")]
                for f in sorted(video_fmts,
                                key=lambda f: f.get("height") or 0, reverse=True):
                    h     = f.get("height") or 0
                    label = _height_label(h) if h else f.get("format_note") or f["format_id"]
                    choices.append((label, f["format_id"]))

            if not choices:
                choices.append(("Best available", "bestvideo+bestaudio/best"))

            self.finished.emit(choices, title)
        except Exception as e:
            self.error.emit(str(e))


class _VideoDownloadWorker(QThread):
    finished = Signal()
    error    = Signal(str)
    progress = Signal(int)

    def __init__(self, url: str, format_id: str, out_path: str, audio_only: bool = False):
        super().__init__()
        self._url        = url
        self._format_id  = format_id
        self._out_path   = out_path
        self._audio_only = audio_only

    def run(self):
        try:
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

            def _hook(d):
                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    if total:
                        self.progress.emit(int(d.get("downloaded_bytes", 0) / total * 100))
                elif d["status"] == "finished":
                    self.progress.emit(99)

            if self._audio_only:
                ydl_opts = {
                    "format": self._format_id,
                    "outtmpl": self._out_path,
                    "ffmpeg_location": ffmpeg,
                    "overwrites": True, "quiet": True, "no_warnings": True,
                    "progress_hooks": [_hook],
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                }
            else:
                ydl_opts = {
                    "format": self._format_id,
                    "outtmpl": self._out_path,
                    "merge_output_format": "mp4",
                    "ffmpeg_location": ffmpeg,
                    "overwrites": True, "quiet": True, "no_warnings": True,
                    "progress_hooks": [_hook],
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self._url])
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ── Progress row helper ────────────────────────────────────────────────────────

def _progress_row(label: str, accent: str) -> tuple:
    """Returns (QFrame container, QProgressBar)."""
    row = QFrame()
    row.setVisible(False)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    lbl = QLabel(label)
    lbl.setFixedWidth(38)
    lbl.setStyleSheet(f"color:{accent}; font-size:12px; font-weight:bold;")
    layout.addWidget(lbl)

    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(0)
    bar.setTextVisible(True)
    bar.setFixedHeight(22)
    bar.setStyleSheet(
        f"QProgressBar {{ border:1px solid #3a3a3a; border-radius:6px; "
        f"background:#1C1C1E; color:white; text-align:center; }}"
        f"QProgressBar::chunk {{ background:{accent}; border-radius:5px; }}"
    )
    layout.addWidget(bar)
    return row, bar


# ── Feature widget ─────────────────────────────────────────────────────────────

class VideoDownloaderFeature(BaseFeature):
    NAV_NAME = "Media Downloader"

    def __init__(self):
        super().__init__()
        self._formats: list[tuple[str, str]] = []
        self._video_title: str = "video"
        # pending save paths set before workers start
        self._mp4_path: str = ""
        self._mp3_path: str = ""
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────────────
        root.addWidget(QLabel("<h1>Media Downloader</h1>"))
        sub = QLabel("YouTube, Instagram, TikTok, Twitter/X, Vimeo and 1000+ platforms.")
        sub.setStyleSheet(f"color:{_MUTED}; font-size:13px;")
        root.addWidget(sub)

        # ── Format selector cards ─────────────────────────────────────────────
        fmt_grid = QGridLayout()
        fmt_grid.setSpacing(12)
        fmt_grid.setColumnStretch(0, 1)
        fmt_grid.setColumnStretch(1, 1)

        self._card_video = _SelectCard("▶", _COLOR_VIDEO, "Video", "Download as MP4")
        self._card_audio = _SelectCard("♪", _COLOR_AUDIO, "Audio", "Download as MP3")
        fmt_grid.addWidget(self._card_video, 0, 0)
        fmt_grid.addWidget(self._card_audio, 0, 1)
        root.addLayout(fmt_grid)

        # ── URL + Fetch ───────────────────────────────────────────────────────
        url_row = QHBoxLayout()
        url_row.setSpacing(10)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("Paste a video URL…")
        self._url_input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:11px 14px; border-radius:8px; color:white; font-size:13px;"
        )
        url_row.addWidget(self._url_input)

        self._btn_fetch = QPushButton("Fetch")
        self._btn_fetch.setFixedWidth(90)
        self._btn_fetch.setStyleSheet(
            f"background:#004545; color:{_ACCENT}; border-radius:8px; "
            f"padding:11px; font-weight:bold; font-size:13px; border:none;"
        )
        self._btn_fetch.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_fetch.clicked.connect(self._fetch_qualities)
        url_row.addWidget(self._btn_fetch)
        root.addLayout(url_row)

        # ── Quality card (shown after fetch) ──────────────────────────────────
        self._quality_card = QFrame()
        self._quality_card.setStyleSheet(
            f"QFrame {{ background:{_BG_CARD}; border-radius:10px; border:none; }}"
        )
        self._quality_card.setVisible(False)
        q_layout = QVBoxLayout(self._quality_card)
        q_layout.setContentsMargins(20, 14, 20, 14)
        q_layout.setSpacing(10)

        self._title_label = QLabel("")
        self._title_label.setStyleSheet(
            "color:white; font-size:13px; font-weight:bold; "
            "background:transparent; border:none;"
        )
        q_layout.addWidget(self._title_label)

        self._quality_combo = QComboBox()
        self._quality_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:8px 12px; border-radius:7px; color:white; font-size:13px;"
        )
        q_layout.addWidget(self._quality_combo)
        root.addWidget(self._quality_card)

        root.addStretch()

        # ── Progress rows ─────────────────────────────────────────────────────
        self._mp4_row, self._mp4_bar = _progress_row("MP4", _ACCENT)
        self._mp3_row, self._mp3_bar = _progress_row("MP3", _COLOR_AUDIO)
        root.addWidget(self._mp4_row)
        root.addWidget(self._mp3_row)

        # ── Status ────────────────────────────────────────────────────────────
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"color:{_MUTED}; font-size:13px;")
        self._status_label.setVisible(False)
        root.addWidget(self._status_label)

        # ── Download button ───────────────────────────────────────────────────
        self._btn_download = self.primary_button("Download", self._download)
        self._btn_download.setEnabled(False)
        root.addWidget(self._btn_download)

    # ── Fetch ──────────────────────────────────────────────────────────────────

    def _fetch_qualities(self):
        url = self._url_input.text().strip()
        if not url:
            self._show_status("Paste a URL first.", error=False)
            return
        if not self._card_video.selected and not self._card_audio.selected:
            self._show_status("Select Video, Audio or both first.", error=False)
            return

        self._hide_status()
        self._btn_fetch.setEnabled(False)
        self._btn_fetch.setText("…")
        self._quality_card.setVisible(False)
        self._btn_download.setEnabled(False)

        self._fetch_worker = _VideoFetchWorker(url)
        self._fetch_worker.finished.connect(self._on_formats_ready)
        self._fetch_worker.error.connect(self._on_fetch_error)
        self._fetch_worker.start()

    def _on_formats_ready(self, formats: list, title: str):
        self._btn_fetch.setEnabled(True)
        self._btn_fetch.setText("Fetch")
        self._formats = formats
        self._video_title = title

        self._quality_combo.clear()
        if self._card_video.selected:
            for label, _ in formats:
                self._quality_combo.addItem(label)
        else:
            self._quality_combo.addItem("Best quality")

        self._title_label.setText(title)
        self._quality_card.setVisible(True)
        self._btn_download.setEnabled(True)

    def _on_fetch_error(self, msg: str):
        self._btn_fetch.setEnabled(True)
        self._btn_fetch.setText("Fetch")
        lower = msg.lower()
        if any(w in lower for w in ("unsupported", "no video formats", "unable to extract")):
            self._show_status("Platform not supported.", error=True)
        else:
            self._show_status(f"Could not fetch: {msg}", error=True)

    # ── Download ───────────────────────────────────────────────────────────────

    def _download(self):
        url = self._url_input.text().strip()
        if not url:
            return

        want_video = self._card_video.selected
        want_audio = self._card_audio.selected

        if not want_video and not want_audio:
            self._show_status("Select Video, Audio or both first.", error=False)
            return

        stem = _safe_filename(self._video_title)

        # Collect save paths before starting any worker
        if want_video:
            self._mp4_path = self.save_dialog("Save Video As", stem + ".mp4", "MP4 (*.mp4)")
            if not self._mp4_path:
                return

        if want_audio:
            self._mp3_path = self.save_dialog("Save Audio As", stem + ".mp3", "MP3 (*.mp3)")
            if not self._mp3_path:
                return

        self._btn_download.setEnabled(False)
        self._hide_status()
        self._pending = []   # track which workers are still running

        if want_video:
            idx    = self._quality_combo.currentIndex()
            _, fmt = self._formats[idx] if self._formats else (None, "bestvideo+bestaudio/best")
            self._mp4_bar.setValue(0)
            self._mp4_row.setVisible(True)
            self._pending.append("video")

            self._dl_video = _VideoDownloadWorker(url, fmt, self._mp4_path)
            self._dl_video.progress.connect(self._mp4_bar.setValue)
            self._dl_video.finished.connect(lambda: self._on_worker_done("video"))
            self._dl_video.error.connect(lambda m: self._on_worker_err("video", m))
            self._dl_video.start()

        if want_audio:
            self._mp3_bar.setValue(0)
            self._mp3_row.setVisible(True)
            self._pending.append("audio")

            self._dl_audio = _VideoDownloadWorker(
                url, "bestaudio/best", self._mp3_path, audio_only=True
            )
            self._dl_audio.progress.connect(self._mp3_bar.setValue)
            self._dl_audio.finished.connect(lambda: self._on_worker_done("audio"))
            self._dl_audio.error.connect(lambda m: self._on_worker_err("audio", m))
            self._dl_audio.start()

    def _on_worker_done(self, kind: str):
        if kind in self._pending:
            self._pending.remove(kind)
        bar = self._mp4_bar if kind == "video" else self._mp3_bar
        bar.setValue(100)
        if not self._pending:
            self._btn_download.setEnabled(True)
            self._show_status("✅  Download complete.", error=False)

    def _on_worker_err(self, kind: str, msg: str):
        if kind in self._pending:
            self._pending.remove(kind)
        self._btn_download.setEnabled(True)
        self._show_status(f"❌  {msg}", error=True)

    # ── Status helpers ─────────────────────────────────────────────────────────

    def _show_status(self, text: str, error: bool):
        color = "#ff5f57" if error else _ACCENT
        self._status_label.setStyleSheet(f"color:{color}; font-size:13px;")
        self._status_label.setText(text)
        self._status_label.setVisible(True)

    def _hide_status(self):
        self._status_label.setVisible(False)
        self._status_label.setText("")
