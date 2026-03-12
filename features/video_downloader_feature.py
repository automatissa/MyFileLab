import os
import re
from collections import defaultdict

import imageio_ffmpeg
import yt_dlp
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QFont
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QMessageBox, QComboBox, QFrame, QProgressBar
)

from .base_feature import BaseFeature

# ── Theme constants ────────────────────────────────────────────────────────────
_BG_CARD  = "#2a2a2c"
_BG_INPUT = "#1C1C1E"
_BORDER   = "#444"
_ACCENT   = "#00f6ff"
_MUTED    = "#888"

# ── Platform registry — add new platforms here only ───────────────────────────
# (placeholder, audio_only, brand_color, icon_symbol)
PLATFORMS: dict[str, tuple[str, bool, str, str]] = {
    "YouTube":     ("https://www.youtube.com/watch?v=...",      False, "#FF0000", "▶"),
    "Instagram":   ("https://www.instagram.com/reel/...",       False, "#C13584", "IG"),
    "TikTok":      ("https://www.tiktok.com/@user/video/...",   False, "#010101", "TK"),
    "Twitter/X":   ("https://x.com/user/status/...",            False, "#1D9BF0", "X"),
    "Facebook":    ("https://www.facebook.com/watch?v=...",     False, "#1877F2", "f"),
    "LinkedIn":    ("https://www.linkedin.com/posts/...",       False, "#0A66C2", "in"),
    "Twitch":      ("https://www.twitch.tv/videos/...",         False, "#9146FF", "tv"),
    "Vimeo":       ("https://vimeo.com/...",                    False, "#1AB7EA", "Vi"),
    "Dailymotion": ("https://www.dailymotion.com/video/...",    False, "#0066DC", "DM"),
    "Audio (MP3)": ("Paste any supported video URL…",           True,  "#1DB954", "♪"),
}


def _make_icon(color: str, symbol: str) -> QIcon:
    """Generate a 24×24 filled circle icon with a centered symbol."""
    px = QPixmap(24, 24)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(0, 0, 24, 24)
    p.setPen(QColor("white"))
    font = QFont("Segoe UI", 7, QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, symbol)
    p.end()
    return QIcon(px)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_filename(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip() or "video"


def _height_label(h: int) -> str:
    labels = {2160: "4K (2160p)", 1440: "2K (1440p)", 1080: "Full HD (1080p)",
              720: "HD (720p)", 480: "480p", 360: "360p", 240: "240p", 144: "144p"}
    return labels.get(h, f"{h}p")


# ── Background workers ────────────────────────────────────────────────────────

class _VideoFetchWorker(QThread):
    finished = Signal(list, str)   # (choices, video_title)
    error    = Signal(str)

    def __init__(self, url: str, audio_only: bool = False):
        super().__init__()
        self._url        = url
        self._audio_only = audio_only

    def run(self):
        try:
            ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self._url, download=False)

            title = info.get("title") or "audio"

            if self._audio_only:
                self.finished.emit([("Best quality", "bestaudio/best")], title)
                return

            formats = info.get("formats", [])

            # Best audio stream (prefer m4a/mp4a for MP4 container compatibility)
            audio_only = [
                f for f in formats
                if f.get("acodec") not in (None, "none")
                and f.get("vcodec") in (None, "none")
            ]
            best_audio = None
            if audio_only:
                m4a = [f for f in audio_only
                       if f.get("ext") == "m4a" or "mp4a" in (f.get("acodec") or "")]
                pool = m4a if m4a else audio_only
                best_audio = max(pool, key=lambda f: f.get("abr") or f.get("tbr") or 0)

            # Group video streams by height
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
                    best_video = max(
                        by_height[h],
                        key=lambda f: f.get("vbr") or f.get("tbr") or 0
                    )
                    vid_id = best_video["format_id"]
                    fmt_id = f"{vid_id}+{best_audio['format_id']}" if best_audio else vid_id
                    choices.append((_height_label(h), fmt_id))
            else:
                # Fallback for platforms that serve a single pre-merged stream
                video_fmts = [f for f in formats if f.get("vcodec") not in (None, "none")]
                for f in sorted(video_fmts, key=lambda f: f.get("height") or 0, reverse=True):
                    h = f.get("height") or 0
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
    progress = Signal(int)    # 0–100

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
                    self.progress.emit(99)   # merging / converting…

            if self._audio_only:
                ydl_opts = {
                    "format": self._format_id,
                    "outtmpl": self._out_path,
                    "ffmpeg_location": ffmpeg,
                    "overwrites": True,
                    "quiet": True,
                    "no_warnings": True,
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
                    "overwrites": True,
                    "quiet": True,
                    "no_warnings": True,
                    "progress_hooks": [_hook],
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self._url])
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ── Feature widget ─────────────────────────────────────────────────────────────

class VideoDownloaderFeature(BaseFeature):
    NAV_NAME = "Video Downloader"

    def __init__(self):
        super().__init__()
        self._formats: list[tuple[str, str]] = []
        self._video_title: str = "video"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>Video Downloader</h1>"))
        layout.addWidget(QLabel(
            "Select a platform, paste the URL, fetch qualities, then download."
        ))

        # ── Platform selector ─────────────────────────────────────────────────
        platform_card = QFrame()
        platform_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        platform_layout = QVBoxLayout(platform_card)
        platform_layout.setContentsMargins(16, 14, 16, 14)
        platform_layout.setSpacing(10)
        platform_layout.addWidget(QLabel("Platform"))

        self._platform_combo = QComboBox()
        for name, (_, __, color, symbol) in PLATFORMS.items():
            self._platform_combo.addItem(_make_icon(color, symbol), name)
        self._platform_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:8px; border-radius:6px; color:white;"
        )
        self._platform_combo.currentTextChanged.connect(self._on_platform_changed)
        platform_layout.addWidget(self._platform_combo)
        layout.addWidget(platform_card)

        # ── URL card ─────────────────────────────────────────────────────────
        url_card = QFrame()
        url_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        url_layout = QVBoxLayout(url_card)
        url_layout.setContentsMargins(16, 14, 16, 14)
        url_layout.setSpacing(10)
        self._url_label_widget = QLabel("Video URL")
        url_layout.addWidget(self._url_label_widget)

        url_row = QHBoxLayout()
        self._url_input = QLineEdit()
        self._url_input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:10px; border-radius:6px; color:white;"
        )
        url_row.addWidget(self._url_input)

        btn_fetch = QPushButton("Fetch Qualities")
        btn_fetch.setFixedWidth(140)
        btn_fetch.setStyleSheet(
            f"background:#004545; color:{_ACCENT}; border-radius:6px; "
            f"padding:10px; font-weight:bold;"
        )
        btn_fetch.clicked.connect(self._fetch_qualities)
        url_row.addWidget(btn_fetch)
        url_layout.addLayout(url_row)
        layout.addWidget(url_card)

        # ── Quality card ─────────────────────────────────────────────────────
        quality_card = QFrame()
        quality_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        quality_layout = QVBoxLayout(quality_card)
        quality_layout.setContentsMargins(16, 14, 16, 14)
        quality_layout.setSpacing(10)
        quality_layout.addWidget(QLabel("Available Quality"))

        self._quality_combo = QComboBox()
        self._quality_combo.setEnabled(False)
        self._quality_combo.addItem("— fetch qualities first —")
        self._quality_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:8px; border-radius:6px; color:white;"
        )
        quality_layout.addWidget(self._quality_combo)

        self._title_label = QLabel("")
        self._title_label.setStyleSheet(f"color:{_MUTED}; font-size:12px;")
        quality_layout.addWidget(self._title_label)
        layout.addWidget(quality_card)

        layout.addStretch()

        # ── Progress bar ──────────────────────────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setVisible(False)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ border:1px solid {_BORDER}; border-radius:6px; "
            f"background:{_BG_INPUT}; color:white; text-align:center; height:22px; }}"
            f"QProgressBar::chunk {{ background:{_ACCENT}; border-radius:5px; }}"
        )
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"color:{_MUTED}; font-size:12px;")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        # ── Download button ───────────────────────────────────────────────────
        self._btn_download = QPushButton("Download")
        self._btn_download.setObjectName("Primary")
        self._btn_download.clicked.connect(self._download)
        layout.addWidget(self._btn_download)

        self._on_platform_changed(self._platform_combo.currentText())

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _on_platform_changed(self, platform: str):
        placeholder, is_audio, *_ = PLATFORMS.get(platform, ("https://...", False, "", ""))
        self._url_input.setPlaceholderText(placeholder)
        self._url_label_widget.setText("Audio URL" if is_audio else "Video URL")
        self._btn_download.setText("Download MP3" if is_audio else "Download MP4")
        self._url_input.clear()
        self._formats = []
        self._video_title = "video"
        self._quality_combo.setEnabled(False)
        self._quality_combo.clear()
        self._quality_combo.addItem("— fetch qualities first —")
        self._title_label.setText("")

    def _fetch_qualities(self):
        url = self._url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a URL.")
            return

        platform = self._platform_combo.currentText()
        _, is_audio, *__ = PLATFORMS.get(platform, ("", False, "", ""))

        self._quality_combo.setEnabled(False)
        self._quality_combo.clear()
        self._quality_combo.addItem("Fetching…")
        self._title_label.setText("")

        self._fetch_worker = _VideoFetchWorker(url, audio_only=is_audio)
        self._fetch_worker.finished.connect(self._on_formats_ready)
        self._fetch_worker.error.connect(self._on_fetch_error)
        self._fetch_worker.start()

    def _on_formats_ready(self, formats: list, title: str):
        self._formats = formats
        self._video_title = title
        self._quality_combo.clear()
        if not formats:
            self._quality_combo.addItem("No downloadable formats found")
            return
        for label, _ in formats:
            self._quality_combo.addItem(label)
        self._quality_combo.setEnabled(True)
        self._title_label.setText(f"Title: {title}")

    def _on_fetch_error(self, msg: str):
        self._quality_combo.clear()
        self._quality_combo.addItem("— error fetching qualities —")
        QMessageBox.critical(self, "Error", f"Could not fetch info:\n{msg}")

    def _download(self):
        url = self._url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a URL.")
            return
        if not self._formats:
            QMessageBox.warning(self, "Warning", "Please fetch qualities first.")
            return

        platform = self._platform_combo.currentText()
        _, is_audio, *__ = PLATFORMS.get(platform, ("", False, "", ""))

        idx = self._quality_combo.currentIndex()
        _, format_id = self._formats[idx]

        ext          = "mp3" if is_audio else "mp4"
        file_filter  = "MP3 (*.mp3)" if is_audio else "MP4 (*.mp4)"
        dialog_title = "Save Audio As" if is_audio else "Save Video As"

        out_path = self.save_dialog(
            dialog_title,
            _safe_filename(self._video_title) + f".{ext}",
            file_filter
        )
        if not out_path:
            return

        self._btn_download.setEnabled(False)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(True)
        self._status_label.setText("Downloading…")
        self._status_label.setVisible(True)

        self._dl_worker = _VideoDownloadWorker(url, format_id, out_path, audio_only=is_audio)
        self._dl_worker.progress.connect(self._on_progress)
        self._dl_worker.finished.connect(lambda: self._on_done(True, ""))
        self._dl_worker.error.connect(lambda m: self._on_done(False, m))
        self._dl_worker.start()

    def _on_progress(self, pct: int):
        self._progress_bar.setValue(pct)
        if pct >= 99:
            self._status_label.setText("Finalising…")

    def _on_done(self, success: bool, msg: str):
        self._btn_download.setEnabled(True)
        self._progress_bar.setVisible(False)
        self._status_label.setVisible(False)
        if success:
            QMessageBox.information(self, "Success", "Download completed successfully!")
        else:
            QMessageBox.critical(self, "Error", msg)
