import os
from pypdf import PdfReader, PdfWriter

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QLineEdit
)

from .base_feature import BaseFeature


class DeletePagesFeature(BaseFeature):
    NAV_NAME = "Delete Pages"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<h1>Delete Pages</h1>"))
        layout.addWidget(QLabel(
            "Remove specific pages from a PDF. "
            "Supports single pages and ranges (e.g. <b>1, 3, 5-10</b>)."
        ))

        # File selector row
        self._file_input = QLineEdit()
        self._file_input.setPlaceholderText("Click to select a PDF file...")
        self._file_input.setReadOnly(True)

        btn_select = QPushButton("Choose File")
        btn_select.clicked.connect(self._select_file)

        row = QHBoxLayout()
        row.addWidget(self._file_input)
        row.addWidget(btn_select)
        layout.addLayout(row)

        # Pages input
        self._pages_input = QLineEdit()
        self._pages_input.setPlaceholderText("Pages to delete (e.g. 1, 3, 5-10)")
        layout.addWidget(self._pages_input)

        layout.addStretch()

        btn_run = QPushButton("Generate New PDF")
        btn_run.setObjectName("Primary")
        btn_run.clicked.connect(self._delete_pages)
        layout.addWidget(btn_run)

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _select_file(self):
        path = self.open_file_dialog("Select a PDF", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)

    def _parse_pages(self, raw: str) -> list[int]:
        pages = []
        for part in raw.replace(" ", "").split(","):
            if "-" in part:
                a, b = part.split("-", 1)
                pages.extend(range(int(a), int(b) + 1))
            else:
                pages.append(int(part))
        return pages

    def _delete_pages(self):
        src = self._file_input.text()
        raw_pages = self._pages_input.text()

        if not src:
            QMessageBox.warning(self, "Warning", "Please select a source file.")
            return
        if not raw_pages:
            QMessageBox.warning(self, "Warning", "Please specify pages to delete.")
            return

        try:
            pages = self._parse_pages(raw_pages)
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid page format. Use numbers and ranges like: 1, 3, 5-10")
            return

        out = self.save_dialog("Save As", "Modified_PDF.pdf", "PDF (*.pdf)")
        if not out:
            return

        def do_work():
            reader = PdfReader(src)
            total = len(reader.pages)
            to_remove = {p - 1 for p in pages if 1 <= p <= total}
            to_keep = [i for i in range(total) if i not in to_remove]
            if not to_keep:
                raise ValueError("Cannot delete all pages from the document.")
            writer = PdfWriter()
            for i in to_keep:
                writer.add_page(reader.pages[i])
            with open(out, "wb") as f:
                writer.write(f)
            writer.close()

        self.run_with_dialog(do_work, "Pages deleted successfully!")
