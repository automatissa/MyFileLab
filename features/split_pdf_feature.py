import os
from pypdf import PdfReader, PdfWriter

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QLineEdit, QComboBox, QFrame
)

from .base_feature import BaseFeature

_BG_CARD  = "#2a2a2c"
_BG_INPUT = "#1C1C1E"
_BORDER   = "#444"
_MUTED    = "#888"


def _parse_ranges(text: str, total: int) -> list[list[int]]:
    """
    Parse a range string like "1-3, 5, 7-9" into groups of 0-based page indices.
    Each comma-separated token becomes one output PDF.
    Raises ValueError on invalid input.
    """
    groups = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            parts = token.split("-", 1)
            start, end = int(parts[0]), int(parts[1])
        else:
            start = end = int(token)
        if start < 1 or end > total or start > end:
            raise ValueError(f"Range '{token}' is out of bounds (1–{total}).")
        groups.append(list(range(start - 1, end)))   # convert to 0-based
    return groups


class SplitPdfFeature(BaseFeature):
    NAV_NAME = "Split PDF"

    def __init__(self):
        super().__init__()
        self._total_pages = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>Split PDF</h1>"))
        layout.addWidget(QLabel(
            "Split a PDF into individual pages, or extract specific page ranges."
        ))

        # ── File picker ───────────────────────────────────────────────────────
        file_card = QFrame()
        file_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(16, 14, 16, 14)
        file_layout.setSpacing(10)
        file_layout.addWidget(QLabel("PDF File"))

        file_row = QHBoxLayout()
        self._file_input = QLineEdit()
        self._file_input.setPlaceholderText("Select a PDF file…")
        self._file_input.setReadOnly(True)
        self._file_input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:10px; border-radius:6px; color:white;"
        )
        file_row.addWidget(self._file_input)

        btn_browse = QPushButton("Browse")
        btn_browse.setFixedWidth(100)
        btn_browse.setStyleSheet("background:#333; color:white; border-radius:6px; padding:10px;")
        btn_browse.clicked.connect(self._browse)
        file_row.addWidget(btn_browse)
        file_layout.addLayout(file_row)

        self._pages_label = QLabel("")
        self._pages_label.setStyleSheet(f"color:{_MUTED}; font-size:12px;")
        file_layout.addWidget(self._pages_label)
        layout.addWidget(file_card)

        # ── Mode selector ─────────────────────────────────────────────────────
        mode_card = QFrame()
        mode_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(16, 14, 16, 14)
        mode_layout.setSpacing(10)
        mode_layout.addWidget(QLabel("Split Mode"))

        self._mode_combo = QComboBox()
        self._mode_combo.addItems([
            "Split into individual pages",
            "Extract page ranges  (e.g.  1-3, 5, 7-9)",
        ])
        self._mode_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:8px; border-radius:6px; color:white;"
        )
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self._mode_combo)

        self._range_input = QLineEdit()
        self._range_input.setPlaceholderText("e.g.  1-3, 5, 7-9   →  creates 3 PDFs")
        self._range_input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:10px; border-radius:6px; color:white;"
        )
        self._range_input.setVisible(False)
        mode_layout.addWidget(self._range_input)
        layout.addWidget(mode_card)

        layout.addStretch()

        btn_split = QPushButton("Split PDF")
        btn_split.setObjectName("Primary")
        btn_split.clicked.connect(self._split)
        layout.addWidget(btn_split)

    def _browse(self):
        path = self.open_file_dialog("Select a PDF", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)
            reader = PdfReader(path)
            self._total_pages = len(reader.pages)
            self._pages_label.setText(f"{self._total_pages} pages")

    def _on_mode_changed(self, index: int):
        self._range_input.setVisible(index == 1)

    def _split(self):
        src = self._file_input.text().strip()
        if not src:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")
            return
        if not self._total_pages:
            QMessageBox.warning(self, "Warning", "Please select a PDF file first.")
            return

        mode = self._mode_combo.currentIndex()

        if mode == 0:
            # Split all → save into a folder
            out_dir = self.folder_dialog("Select Output Folder")
            if not out_dir:
                return
            self._run_split_all(src, out_dir)
        else:
            # Extract ranges → parse, save each range as a separate file
            raw = self._range_input.text().strip()
            if not raw:
                QMessageBox.warning(self, "Warning", "Please enter at least one page range.")
                return
            try:
                groups = _parse_ranges(raw, self._total_pages)
            except ValueError as e:
                QMessageBox.critical(self, "Invalid Range", str(e))
                return
            if not groups:
                QMessageBox.warning(self, "Warning", "No valid ranges found.")
                return
            out_dir = self.folder_dialog("Select Output Folder")
            if not out_dir:
                return
            self._run_split_ranges(src, out_dir, groups)

    def _run_split_all(self, src: str, out_dir: str):
        base = os.path.splitext(os.path.basename(src))[0]

        def _run():
            reader = PdfReader(src)
            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                dest = os.path.join(out_dir, f"{base}_page_{i}.pdf")
                with open(dest, "wb") as f:
                    writer.write(f)

        self.run_with_dialog(_run, f"Split into {self._total_pages} files in:\n{out_dir}")

    def _run_split_ranges(self, src: str, out_dir: str, groups: list):
        base = os.path.splitext(os.path.basename(src))[0]

        def _run():
            reader = PdfReader(src)
            for idx, pages in enumerate(groups, start=1):
                writer = PdfWriter()
                for p in pages:
                    writer.add_page(reader.pages[p])
                first = pages[0] + 1
                last  = pages[-1] + 1
                name  = f"{base}_p{first}-{last}.pdf" if first != last else f"{base}_p{first}.pdf"
                dest  = os.path.join(out_dir, name)
                with open(dest, "wb") as f:
                    writer.write(f)

        self.run_with_dialog(_run, f"Saved {len(groups)} PDF(s) to:\n{out_dir}")
