import os
import fitz  # PyMuPDF

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QLineEdit
)

from .base_feature import BaseFeature


class PdfToMdFeature(BaseFeature):
    NAV_NAME = "PDF to MD"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<h1>Convert PDF to Markdown</h1>"))
        layout.addWidget(QLabel(
            "Extract text from your PDF and save it as a <b>.md</b> Markdown file."
        ))

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
            "Save Markdown",
            src.replace(".pdf", ".md"),
            "Markdown (*.md)",
        )
        if not dest:
            return

        def do_work():
            doc = fitz.open(src)
            output = []
            for page_num, page in enumerate(doc, start=1):
                output.append(f"## Page {page_num}\n\n")
                for block in page.get_text("blocks"):
                    text = block[4].strip()
                    if text:
                        output.append(text + "\n\n")
                output.append("---\n\n")
            doc.close()
            with open(dest, "w", encoding="utf-8") as f:
                f.writelines(output)

        self.run_with_dialog(do_work, f"Conversion complete!\nFile: {os.path.basename(dest)}")
