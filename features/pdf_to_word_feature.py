import os
from pdf2docx import Converter

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QLineEdit
)


from .base_feature import BaseFeature


class PdfToWordFeature(BaseFeature):
    NAV_NAME = "PDF to Word"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<h1>Convert PDF to Word</h1>"))
        layout.addWidget(QLabel(
            "Instantly transform your PDF files into editable <b>.docx</b> documents."
        ))

        # File selector row
        self._file_input = QLineEdit()
        self._file_input.setPlaceholderText("Select a PDF file...")
        self._file_input.setReadOnly(True)

        btn_select = QPushButton("Choose File")
        btn_select.clicked.connect(self._select_file)

        row = QHBoxLayout()
        row.addWidget(self._file_input)
        row.addWidget(btn_select)
        layout.addLayout(row)

        layout.addStretch()

        btn_run = QPushButton("Convert Now")
        btn_run.setObjectName("Primary")
        btn_run.clicked.connect(self._convert)
        layout.addWidget(btn_run)

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a PDF", "", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)

    def _convert(self):
        src = self._file_input.text()
        if not src:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")
            return

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Save Word Document",
            src.replace(".pdf", ".docx"),
            "Word (*.docx)",
        )
        if not dest:
            return

        def do_work():
            cv = Converter(src)
            cv.convert(dest, start=0, multi_processing=False)
            cv.close()

        self.run_with_dialog(do_work, f"Conversion complete!\nFile: {os.path.basename(dest)}")
