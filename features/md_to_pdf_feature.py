import os
import fitz  # PyMuPDF
import markdown

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QLineEdit
)

from .base_feature import BaseFeature


class MdToPdfFeature(BaseFeature):
    NAV_NAME = "MD to PDF"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<h1>Convert Markdown to PDF</h1>"))
        layout.addWidget(QLabel(
            "Transform your <b>.md</b> Markdown files into formatted PDF documents."
        ))

        self._file_input = QLineEdit()
        self._file_input.setPlaceholderText("Select a Markdown file...")
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
        path = self.open_file_dialog("Select a Markdown file", "Markdown (*.md *.markdown)")
        if path:
            self._file_input.setText(path)

    def _convert(self):
        src = self._file_input.text()
        if not src:
            QMessageBox.warning(self, "Warning", "Please select a Markdown file.")
            return

        dest = self.save_dialog("Save PDF", os.path.splitext(src)[0] + ".pdf", "PDF (*.pdf)")
        if not dest:
            return

        def do_work():
            with open(src, "r", encoding="utf-8") as f:
                md_text = f.read()
            html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
            html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12pt; line-height: 1.6; margin: 40px; }}
  h1, h2, h3 {{ color: #222; }}
  code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
  pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; }}
  th {{ background: #eee; }}
  hr {{ border: none; border-top: 1px solid #ccc; }}
</style>
</head><body>{html_body}</body></html>"""
            story = fitz.Story(html=html)
            writer = fitz.DocumentWriter(dest)
            mediabox = fitz.paper_rect("a4")
            margin = 50
            where = mediabox + (margin, margin, -margin, -margin)
            more = 1
            while more:
                dev = writer.begin_page(mediabox)
                more, _ = story.place(where)
                story.draw(dev)
                writer.end_page()
            writer.close()

        self.run_with_dialog(do_work, f"Conversion complete!\nFile: {os.path.basename(dest)}")
