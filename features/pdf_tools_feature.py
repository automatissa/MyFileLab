import os

import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton,
    QLabel, QLineEdit, QFrame, QGridLayout, QScrollArea,
    QWidget, QMessageBox, QComboBox, QSizePolicy
)

from .base_feature import BaseFeature, ConversionWorker, ProcessingDialog, AppCard

_ACCENT   = "#00f6ff"
_BG_CARD  = "#2a2a2c"
_BG_INPUT = "#1C1C1E"
_BORDER   = "#444"
_MUTED    = "#888"

_COLOR_MERGE    = "#2B579A"
_COLOR_SPLIT    = "#C43E1C"
_COLOR_DELETE   = "#B91C1C"
_COLOR_COMPRESS = "#217346"
_COLOR_OCR      = "#7C3AED"


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _file_card(label="PDF File", placeholder="Select a PDF file…"):
    """Returns (QFrame card, QLineEdit input, info_label) ready to drop into a layout."""
    card = QFrame()
    card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
    cl = QVBoxLayout(card)
    cl.setContentsMargins(16, 14, 16, 14)
    cl.setSpacing(10)
    cl.addWidget(QLabel(label))

    row = QHBoxLayout()
    inp = QLineEdit()
    inp.setPlaceholderText(placeholder)
    inp.setReadOnly(True)
    inp.setStyleSheet(
        f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
        f"padding:10px; border-radius:6px; color:white;"
    )
    row.addWidget(inp)

    btn = QPushButton("Browse")
    btn.setFixedWidth(100)
    btn.setStyleSheet("background:#333; color:white; border-radius:6px; padding:10px; border:none;")
    row.addWidget(btn)
    cl.addLayout(row)

    info = QLabel("")
    info.setStyleSheet(f"color:{_MUTED}; font-size:12px; background:transparent;")
    cl.addWidget(info)

    return card, inp, info, btn


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL PANELS
# ══════════════════════════════════════════════════════════════════════════════

class _MergePanel(BaseFeature):
    NAV_NAME = ""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<h1>Merge PDFs</h1>"))
        layout.addWidget(QLabel(
            "Add PDFs, set optional page ranges per file (e.g. <b>1-3, 5</b>), "
            "then use ↑ ↓ to reorder."
        ))

        self._drop_zone = _DropZone()
        layout.addWidget(self._drop_zone)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("Add Files")
        btn_add.clicked.connect(self._add_files)
        btn_clear = QPushButton("Clear List")
        btn_clear.clicked.connect(self._drop_zone.clear_all)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addWidget(self.primary_button("Execute Merge", self._merge))

    def _add_files(self):
        for path in self.open_files_dialog("Select PDF Files", "PDF (*.pdf)"):
            self._drop_zone.add_file(path)

    def _parse_pages(self, raw: str, total: int) -> list:
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


class _FileRow(QFrame):
    def __init__(self, filepath, on_move_up, on_move_down, on_remove, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.setStyleSheet("background:#2a2a2c; border-radius:8px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        for symbol, cb in [("↑", on_move_up), ("↓", on_move_down)]:
            btn = QPushButton(symbol)
            btn.setFixedSize(26, 26)
            btn.setStyleSheet("background:#333; color:white; border-radius:5px; font-weight:bold; padding:0; border:none;")
            btn.clicked.connect(cb)
            layout.addWidget(btn)
        name = QLabel(os.path.basename(filepath))
        name.setToolTip(filepath)
        name.setStyleSheet("color:white; background:transparent;")
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(name)
        self._pages = QLineEdit()
        self._pages.setPlaceholderText("Pages: all  (e.g. 1-3, 5)")
        self._pages.setFixedWidth(210)
        self._pages.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; padding:5px; border-radius:5px; color:white;"
        )
        layout.addWidget(self._pages)
        btn_rm = QPushButton("✕")
        btn_rm.setFixedSize(28, 28)
        btn_rm.setStyleSheet("background:#3a1a1a; color:#ff6b6b; border-radius:5px; font-weight:bold; padding:0; border:none;")
        btn_rm.clicked.connect(on_remove)
        layout.addWidget(btn_rm)

    def pages_text(self):
        return self._pages.text()


class _DropZone(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setMinimumHeight(300)
        self.setStyleSheet(
            f"QScrollArea {{ background:{_BG_INPUT}; border:2px dashed {_BORDER}; border-radius:10px; }}"
        )
        self._container = QWidget()
        self._container.setStyleSheet("background:transparent;")
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._vbox.setSpacing(6)
        self._vbox.setContentsMargins(8, 8, 8, 8)
        self._placeholder = QLabel("Drop PDF files here or use \"Add Files\"")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(f"color:{_MUTED}; font-size:14px; padding:60px;")
        self._vbox.addWidget(self._placeholder)
        self.setWidget(self._container)
        self._rows: list = []

    def add_file(self, filepath):
        if self._placeholder.isVisible():
            self._placeholder.hide()
        row = _FileRow(filepath,
                       on_move_up=lambda: self._move(row, -1),
                       on_move_down=lambda: self._move(row, +1),
                       on_remove=lambda: self._remove(row))
        self._rows.append(row)
        self._vbox.addWidget(row)

    def entries(self):
        return [(r.filepath, r.pages_text()) for r in self._rows]

    def clear_all(self):
        for row in list(self._rows):
            row.deleteLater()
        self._rows.clear()
        self._placeholder.show()

    def _remove(self, row):
        self._rows.remove(row)
        self._vbox.removeWidget(row)
        row.deleteLater()
        if not self._rows:
            self._placeholder.show()

    def _move(self, row, direction):
        idx = self._rows.index(row)
        new_idx = idx + direction
        if not (0 <= new_idx < len(self._rows)):
            return
        self._rows[idx], self._rows[new_idx] = self._rows[new_idx], self._rows[idx]
        for r in self._rows:
            self._vbox.removeWidget(r)
        for r in self._rows:
            self._vbox.addWidget(r)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self.add_file(path)
        event.acceptProposedAction()


class _SplitPanel(BaseFeature):
    NAV_NAME = ""

    def __init__(self):
        super().__init__()
        self._total_pages = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>Split PDF</h1>"))
        layout.addWidget(QLabel("Split a PDF into individual pages, or extract specific page ranges."))

        card, self._file_input, self._pages_label, btn = _file_card()
        btn.clicked.connect(self._browse)
        layout.addWidget(card)

        mode_card = QFrame()
        mode_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        mc = QVBoxLayout(mode_card)
        mc.setContentsMargins(16, 14, 16, 14)
        mc.setSpacing(10)
        mc.addWidget(QLabel("Split Mode"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems([
            "Split into individual pages",
            "Extract page ranges  (e.g.  1-3, 5, 7-9)",
        ])
        self._mode_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; padding:8px; border-radius:6px; color:white;"
        )
        self._mode_combo.currentIndexChanged.connect(lambda i: self._range_input.setVisible(i == 1))
        mc.addWidget(self._mode_combo)
        self._range_input = QLineEdit()
        self._range_input.setPlaceholderText("e.g.  1-3, 5, 7-9   →  creates 3 PDFs")
        self._range_input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; padding:10px; border-radius:6px; color:white;"
        )
        self._range_input.setVisible(False)
        mc.addWidget(self._range_input)
        layout.addWidget(mode_card)
        layout.addStretch()

        layout.addWidget(self.primary_button("Split PDF", self._split))

    def _browse(self):
        path = self.open_file_dialog("Select a PDF", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)
            reader = PdfReader(path)
            self._total_pages = len(reader.pages)
            self._pages_label.setText(f"{self._total_pages} pages")

    def _split(self):
        src = self._file_input.text().strip()
        if not src or not self._total_pages:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")
            return
        if self._mode_combo.currentIndex() == 0:
            out_dir = self.folder_dialog("Select Output Folder")
            if not out_dir:
                return
            base = os.path.splitext(os.path.basename(src))[0]
            def _run():
                reader = PdfReader(src)
                for i, page in enumerate(reader.pages, 1):
                    w = PdfWriter()
                    w.add_page(page)
                    with open(os.path.join(out_dir, f"{base}_page_{i}.pdf"), "wb") as f:
                        w.write(f)
            self.run_with_dialog(_run, f"Split into {self._total_pages} files in:\n{out_dir}")
        else:
            raw = self._range_input.text().strip()
            if not raw:
                QMessageBox.warning(self, "Warning", "Please enter at least one page range.")
                return
            try:
                groups = self._parse_ranges(raw)
            except ValueError as e:
                QMessageBox.critical(self, "Invalid Range", str(e))
                return
            out_dir = self.folder_dialog("Select Output Folder")
            if not out_dir:
                return
            base = os.path.splitext(os.path.basename(src))[0]
            def _run():
                reader = PdfReader(src)
                for pages in groups:
                    w = PdfWriter()
                    for p in pages:
                        w.add_page(reader.pages[p])
                    first, last = pages[0] + 1, pages[-1] + 1
                    name = f"{base}_p{first}-{last}.pdf" if first != last else f"{base}_p{first}.pdf"
                    with open(os.path.join(out_dir, name), "wb") as f:
                        w.write(f)
            self.run_with_dialog(_run, f"Saved {len(groups)} PDF(s) to:\n{out_dir}")

    def _parse_ranges(self, text: str) -> list:
        groups = []
        for token in text.split(","):
            token = token.strip()
            if not token:
                continue
            if "-" in token:
                a, b = token.split("-", 1)
                start, end = int(a), int(b)
            else:
                start = end = int(token)
            if start < 1 or end > self._total_pages or start > end:
                raise ValueError(f"Range '{token}' is out of bounds (1–{self._total_pages}).")
            groups.append(list(range(start - 1, end)))
        return groups


class _DeletePanel(BaseFeature):
    NAV_NAME = ""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>Delete Pages</h1>"))
        layout.addWidget(QLabel(
            "Remove specific pages from a PDF. "
            "Supports single pages and ranges (e.g. <b>1, 3, 5-10</b>)."
        ))

        card, self._file_input, _, btn = _file_card()
        btn.clicked.connect(self._browse)
        layout.addWidget(card)

        pages_card = QFrame()
        pages_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        pc = QVBoxLayout(pages_card)
        pc.setContentsMargins(16, 14, 16, 14)
        pc.setSpacing(10)
        pc.addWidget(QLabel("Pages to Delete"))
        self._pages_input = QLineEdit()
        self._pages_input.setPlaceholderText("e.g.  1, 3, 5-10")
        self._pages_input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; padding:10px; border-radius:6px; color:white;"
        )
        pc.addWidget(self._pages_input)
        layout.addWidget(pages_card)
        layout.addStretch()

        layout.addWidget(self.primary_button("Generate New PDF", self._delete))

    def _browse(self):
        path = self.open_file_dialog("Select a PDF", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)

    def _delete(self):
        src = self._file_input.text().strip()
        raw = self._pages_input.text().strip()
        if not src:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")
            return
        if not raw:
            QMessageBox.warning(self, "Warning", "Please specify pages to delete.")
            return
        try:
            pages = []
            for part in raw.replace(" ", "").split(","):
                if "-" in part:
                    a, b = part.split("-", 1)
                    pages.extend(range(int(a), int(b) + 1))
                else:
                    pages.append(int(part))
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid page format. Use: 1, 3, 5-10")
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


_COMPRESS_PRESETS = {
    "Light   — best quality, smaller size": (1, True, False, False, False),
    "Medium  — balanced":                   (3, True, True,  True,  True),
    "Maximum — smallest file, good quality":(4, True, True,  True,  True),
}

class _CompressPanel(BaseFeature):
    NAV_NAME = ""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>Compress PDF</h1>"))
        layout.addWidget(QLabel("Reduce PDF file size while preserving readability."))

        card, self._file_input, self._size_label, btn = _file_card()
        btn.clicked.connect(self._browse)
        layout.addWidget(card)

        preset_card = QFrame()
        preset_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        pc = QVBoxLayout(preset_card)
        pc.setContentsMargins(16, 14, 16, 14)
        pc.setSpacing(10)
        pc.addWidget(QLabel("Compression Level"))
        self._preset_combo = QComboBox()
        for label in _COMPRESS_PRESETS:
            self._preset_combo.addItem(label)
        self._preset_combo.setCurrentIndex(1)
        self._preset_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; padding:8px; border-radius:6px; color:white;"
        )
        pc.addWidget(self._preset_combo)
        layout.addWidget(preset_card)
        layout.addStretch()

        layout.addWidget(self.primary_button("Compress PDF", self._compress))

    def _browse(self):
        path = self.open_file_dialog("Select a PDF", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)
            self._size_label.setText(f"Current size: {os.path.getsize(path) / 1048576:.2f} MB")

    def _compress(self):
        src = self._file_input.text().strip()
        if not src:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")
            return
        garbage, deflate, clean, deflate_images, deflate_fonts = \
            _COMPRESS_PRESETS[self._preset_combo.currentText()]
        default = os.path.join(
            os.path.dirname(src),
            os.path.splitext(os.path.basename(src))[0] + "_compressed.pdf"
        )
        dest = self.save_dialog("Save Compressed PDF", default, "PDF (*.pdf)")
        if not dest:
            return
        orig_mb = os.path.getsize(src) / 1048576

        def _run():
            doc = fitz.open(src)
            opts = dict(garbage=garbage, deflate=deflate, clean=clean)
            try:
                doc.save(dest, **opts, deflate_images=deflate_images, deflate_fonts=deflate_fonts)
            except TypeError:
                doc.save(dest, **opts)
            doc.close()

        worker = ConversionWorker(_run)
        dialog = ProcessingDialog(self)
        _fired = [False]

        def _done(success, msg):
            if _fired[0]:
                return
            _fired[0] = True
            dialog.accept()
            if success:
                new_mb = os.path.getsize(dest) / 1048576
                pct = max(0.0, (orig_mb - new_mb) / orig_mb * 100) if orig_mb else 0
                QMessageBox.information(self, "Done",
                    f"Compressed!\n\n{orig_mb:.2f} MB  →  {new_mb:.2f} MB  ({pct:.0f}% saved)")
            else:
                QMessageBox.critical(self, "Error", msg)

        worker.finished.connect(lambda: _done(True, ""))
        worker.error.connect(lambda m: _done(False, m))
        worker.start()
        dialog.exec()


_OCR_OUTPUTS = {
    "Text file  (.txt)":      "txt",
    "Searchable PDF  (.pdf)": "pdf",
}


def _find_tesseract() -> tuple:
    """Return (exe_path, env_dict) for subprocess.run.

    env_dict is either None (inherit process env) or a copy with TESSDATA_PREFIX
    set to the bundled tessdata directory (PyInstaller frozen builds only).
    """
    import sys as _sys
    import shutil as _shutil

    # 1. Bundled inside a PyInstaller --onefile exe
    if getattr(_sys, "frozen", False):
        base = os.path.join(_sys._MEIPASS, "tesseract")
        exe = os.path.join(base, "tesseract.exe" if _sys.platform == "win32" else "tesseract")
        if os.path.exists(exe):
            env = os.environ.copy()
            env["TESSDATA_PREFIX"] = base   # tessdata/ is a subdir of base
            return exe, env

    # 2. Already on PATH (system install — tessdata prefix already in env)
    found = _shutil.which("tesseract")
    if found:
        return found, None

    # 3. Common Windows install locations
    if _sys.platform == "win32":
        for candidate in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]:
            if os.path.exists(candidate):
                return candidate, None

    raise RuntimeError(
        "Tesseract not found.\n\n"
        "Download and install Tesseract-OCR from:\n"
        "https://github.com/UB-Mannheim/tesseract/wiki"
    )


class _OcrPanel(BaseFeature):
    NAV_NAME = ""

    def __init__(self):
        super().__init__()
        self._total_pages = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>OCR</h1>"))
        layout.addWidget(QLabel("Extract text from scanned PDFs."))

        card, self._file_input, self._pages_label, btn = _file_card()
        btn.clicked.connect(self._browse)
        layout.addWidget(card)

        out_card = QFrame()
        out_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        oc = QVBoxLayout(out_card)
        oc.setContentsMargins(16, 14, 16, 14)
        oc.setSpacing(10)
        oc.addWidget(QLabel("Output Format"))
        self._format_combo = QComboBox()
        for label in _OCR_OUTPUTS:
            self._format_combo.addItem(label)
        self._format_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; padding:8px; border-radius:6px; color:white;"
        )
        oc.addWidget(self._format_combo)
        layout.addWidget(out_card)
        layout.addStretch()

        layout.addWidget(self.primary_button("Run OCR", self._run_ocr))

    def _browse(self):
        path = self.open_file_dialog("Select a PDF", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)
            self._total_pages = len(PdfReader(path).pages)
            self._pages_label.setText(f"{self._total_pages} pages")

    def _run_ocr(self):
        src = self._file_input.text().strip()
        if not src:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")
            return

        try:
            tesseract, tess_env = _find_tesseract()
        except RuntimeError as e:
            QMessageBox.critical(self, "Tesseract Not Found", str(e))
            return

        fmt = _OCR_OUTPUTS[self._format_combo.currentText()]
        base = os.path.splitext(os.path.basename(src))[0] + "_ocr"
        if fmt == "txt":
            out = self.save_dialog("Save Text File", base + ".txt", "Text (*.txt)")
        else:
            out = self.save_dialog("Save Searchable PDF", base + ".pdf", "PDF (*.pdf)")
        if not out:
            return

        def do_work():
            import subprocess
            import tempfile

            doc = fitz.open(src)
            with tempfile.TemporaryDirectory() as tmp:
                if fmt == "txt":
                    with open(out, "w", encoding="utf-8") as out_f:
                        for i, page in enumerate(doc, 1):
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                            img_path = os.path.join(tmp, f"page_{i}.png")
                            pix.save(img_path)
                            result = subprocess.run(
                                [tesseract, img_path, "stdout"],
                                capture_output=True, text=True, check=True,
                                env=tess_env,
                            )
                            out_f.write(f"--- Page {i} ---\n")
                            out_f.write(result.stdout)
                            out_f.write("\n\n")
                else:
                    # Render all pages, OCR each to a per-page PDF, then merge
                    pdf_parts = []
                    for i, page in enumerate(doc, 1):
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_path = os.path.join(tmp, f"page_{i}.png")
                        pix.save(img_path)
                        out_base = os.path.join(tmp, f"page_{i}")
                        subprocess.run(
                            [tesseract, img_path, out_base, "pdf"],
                            capture_output=True, check=True,
                            env=tess_env,
                        )
                        pdf_parts.append(out_base + ".pdf")
                    writer = PdfWriter()
                    for part in pdf_parts:
                        reader = PdfReader(part)
                        for p in reader.pages:
                            writer.add_page(p)
                    with open(out, "wb") as f:
                        writer.write(f)
            doc.close()

        self.run_with_dialog(do_work, "OCR completed successfully!")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN FEATURE
# ══════════════════════════════════════════════════════════════════════════════

class PdfToolsFeature(BaseFeature):
    NAV_NAME = "PDF Tools"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._stack.addWidget(self._build_launcher())   # index 0

        for panel in [_MergePanel(), _SplitPanel(), _DeletePanel(), _CompressPanel(), _OcrPanel()]:
            self._stack.addWidget(self._wrap(panel))    # index 1-5

    def _wrap(self, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background:#1C1C1E; border-bottom:1px solid #2a2a2c;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 10, 24, 10)
        btn = QPushButton("← Back to PDF Tools")
        btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        btn.setStyleSheet(
            f"background:transparent; color:{_ACCENT}; border:none; "
            f"font-size:13px; font-weight:bold; padding:4px 0;"
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hl.addWidget(btn)
        hl.addStretch()

        layout.addWidget(header)
        layout.addWidget(widget)
        return wrapper

    def _build_launcher(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        layout.addWidget(QLabel("<h1>PDF Tools</h1>"))
        layout.addWidget(QLabel("Select a tool to get started."))

        grid = QGridLayout()
        grid.setSpacing(16)
        for col in range(3):
            grid.setColumnStretch(col, 1)

        cards = [
            AppCard("M",   _COLOR_MERGE,    "Merge PDFs",
                "Combine multiple PDFs. Drag & drop, reorder, set page ranges.",
                lambda: self._stack.setCurrentIndex(1)),
            AppCard("✂",  _COLOR_SPLIT,    "Split PDF",
                "Split into individual pages or extract specific ranges.",
                lambda: self._stack.setCurrentIndex(2)),
            AppCard("✕",  _COLOR_DELETE,   "Delete Pages",
                "Remove one or more pages from a PDF.",
                lambda: self._stack.setCurrentIndex(3)),
            AppCard("↓",  _COLOR_COMPRESS, "Compress PDF",
                "Reduce file size. Shows before/after size and % saved.",
                lambda: self._stack.setCurrentIndex(4)),
            AppCard("OCR", _COLOR_OCR, "OCR",
                "Extract text from scanned PDFs.",
                lambda: self._stack.setCurrentIndex(5)),
        ]

        for i, card in enumerate(cards):
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()
        return scroll
