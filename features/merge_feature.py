import os
from pypdf import PdfReader, PdfWriter

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QScrollArea, QFrame, QLineEdit,
    QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from .base_feature import BaseFeature

# ── Theme constants ────────────────────────────────────────────────────────────
_BG_CARD    = "#2a2a2c"
_BG_INPUT   = "#1C1C1E"
_BORDER     = "#444"
_ACCENT     = "#00f6ff"
_RED        = "#ff6b6b"
_RED_BG     = "#3a1a1a"
_MUTED      = "#888"


class _FileRow(QFrame):
    """One row in the merge list: [↑][↓] filename  [page range input]  [✕]"""

    def __init__(self, filepath: str, on_move_up, on_move_down, on_remove, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.setStyleSheet(
            f"background-color: {_BG_CARD}; border-radius: 8px;"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Move buttons
        for symbol, callback in [("↑", on_move_up), ("↓", on_move_down)]:
            btn = QPushButton(symbol)
            btn.setFixedSize(26, 26)
            btn.setStyleSheet(
                f"background: #333; color: white; border-radius: 5px; font-weight: bold; padding: 0;"
            )
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        # Filename label (shows basename, tooltip = full path)
        name = QLabel(os.path.basename(filepath))
        name.setToolTip(filepath)
        name.setStyleSheet(f"color: white; background: transparent;")
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(name)

        # Page range input
        self._pages = QLineEdit()
        self._pages.setPlaceholderText("Pages: all  (e.g. 1-3, 5)")
        self._pages.setFixedWidth(210)
        self._pages.setStyleSheet(
            f"background: {_BG_INPUT}; border: 1px solid {_BORDER}; "
            f"padding: 5px; border-radius: 5px; color: white;"
        )
        layout.addWidget(self._pages)

        # Remove button
        btn_rm = QPushButton("✕")
        btn_rm.setFixedSize(28, 28)
        btn_rm.setStyleSheet(
            f"background: {_RED_BG}; color: {_RED}; border-radius: 5px; font-weight: bold; padding: 0;"
        )
        btn_rm.clicked.connect(on_remove)
        layout.addWidget(btn_rm)

    def pages_text(self) -> str:
        return self._pages.text()


class _DropZone(QScrollArea):
    """Scrollable list of _FileRow widgets that also accepts external PDF drops."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setMinimumHeight(300)
        self.setStyleSheet(
            f"QScrollArea {{ background-color: {_BG_INPUT}; border: 2px dashed {_BORDER}; border-radius: 10px; }}"
        )

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._vbox.setSpacing(6)
        self._vbox.setContentsMargins(8, 8, 8, 8)

        self._placeholder = QLabel("Drop PDF files here or use  \"Add Files\"")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(f"color: {_MUTED}; font-size: 14px; padding: 60px;")
        self._vbox.addWidget(self._placeholder)

        self.setWidget(self._container)
        self._rows: list[_FileRow] = []

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_file(self, filepath: str):
        if self._placeholder.isVisible():
            self._placeholder.hide()

        row = _FileRow(
            filepath,
            on_move_up=lambda: self._move(row, -1),
            on_move_down=lambda: self._move(row, +1),
            on_remove=lambda: self._remove(row),
        )
        self._rows.append(row)
        self._vbox.addWidget(row)

    def entries(self) -> list[tuple[str, str]]:
        """Returns list of (filepath, pages_text) for each row."""
        return [(r.filepath, r.pages_text()) for r in self._rows]

    def clear_all(self):
        for row in list(self._rows):
            row.deleteLater()
        self._rows.clear()
        self._placeholder.show()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _remove(self, row: _FileRow):
        self._rows.remove(row)
        self._vbox.removeWidget(row)
        row.deleteLater()
        if not self._rows:
            self._placeholder.show()

    def _move(self, row: _FileRow, direction: int):
        idx = self._rows.index(row)
        new_idx = idx + direction
        if not (0 <= new_idx < len(self._rows)):
            return
        # Swap in logical list
        self._rows[idx], self._rows[new_idx] = self._rows[new_idx], self._rows[idx]
        # Rebuild layout order
        for r in self._rows:
            self._vbox.removeWidget(r)
        for r in self._rows:
            self._vbox.addWidget(r)

    # ── Drag & drop (external files) ───────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self.add_file(path)
        event.acceptProposedAction()


class MergeFeature(BaseFeature):
    NAV_NAME = "Merge PDFs"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<h1>Merge Documents</h1>"))
        layout.addWidget(QLabel(
            "Add PDFs, set optional page ranges per file (e.g. <b>1-3, 5</b>), "
            "then use ↑ ↓ to reorder."
        ))

        self._drop_zone = _DropZone()
        layout.addWidget(self._drop_zone)

        # Secondary buttons row
        btn_row = QHBoxLayout()
        btn_add = QPushButton("Add Files")
        btn_add.clicked.connect(self._add_files)
        btn_clear = QPushButton("Clear List")
        btn_clear.clicked.connect(self._drop_zone.clear_all)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Primary action
        btn_merge = QPushButton("Execute Merge")
        btn_merge.setObjectName("Primary")
        btn_merge.clicked.connect(self._merge)
        layout.addWidget(btn_merge)

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _add_files(self):
        paths = self.open_files_dialog("Select PDF Files", "PDF (*.pdf)")
        for path in paths:
            self._drop_zone.add_file(path)

    def _parse_pages(self, raw: str, total: int) -> list[int]:
        """Convert a page-range string to a 0-based index list. Empty = all pages."""
        if not raw.strip():
            return list(range(total))
        indices = []
        for part in raw.replace(" ", "").split(","):
            if "-" in part:
                a, b = part.split("-", 1)
                indices.extend(range(int(a) - 1, int(b)))
            else:
                indices.append(int(part) - 1)
        return [i for i in indices if 0 <= i < total]

    def _merge(self):
        entries = self._drop_zone.entries()
        if not entries:
            QMessageBox.warning(self, "Warning", "The file list is empty.")
            return

        out = self.save_dialog("Save As", "Merged_Result.pdf", "PDF (*.pdf)")
        if not out:
            return

        def do_work():
            writer = PdfWriter()
            try:
                for filepath, raw_pages in entries:
                    if not os.path.exists(filepath):
                        raise FileNotFoundError(f"File not found: {os.path.basename(filepath)}")
                    reader = PdfReader(filepath)
                    for i in self._parse_pages(raw_pages, len(reader.pages)):
                        writer.add_page(reader.pages[i])
                if len(writer.pages) == 0:
                    raise ValueError("The merged document contains no pages.")
                with open(out, "wb") as f:
                    writer.write(f)
            finally:
                writer.close()

        self.run_with_dialog(do_work, "Merge completed successfully!")
