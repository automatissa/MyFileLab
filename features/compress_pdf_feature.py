import os
import fitz  # PyMuPDF

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QLineEdit, QComboBox, QFrame
)

from .base_feature import BaseFeature
from .worker import ConversionWorker
from .processing_dialog import ProcessingDialog

_BG_CARD  = "#2a2a2c"
_BG_INPUT = "#1C1C1E"
_BORDER   = "#444"
_MUTED    = "#888"

# Compression presets: (garbage, deflate, clean, deflate_images, deflate_fonts)
_PRESETS = {
    "Light   — best quality, smaller size": (1, True, False, False, False),
    "Medium  — balanced":                   (3, True, True,  True,  True),
    "Maximum — smallest file, good quality":(4, True, True,  True,  True),
}


class CompressPdfFeature(BaseFeature):
    NAV_NAME = "Compress PDF"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>Compress PDF</h1>"))
        layout.addWidget(QLabel("Reduce PDF file size while preserving readability."))

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
        layout.addWidget(file_card)

        # ── Preset selector ───────────────────────────────────────────────────
        preset_card = QFrame()
        preset_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(16, 14, 16, 14)
        preset_layout.setSpacing(10)
        preset_layout.addWidget(QLabel("Compression Level"))

        self._preset_combo = QComboBox()
        for label in _PRESETS:
            self._preset_combo.addItem(label)
        self._preset_combo.setCurrentIndex(1)
        self._preset_combo.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:8px; border-radius:6px; color:white;"
        )
        preset_layout.addWidget(self._preset_combo)

        self._size_label = QLabel("")
        self._size_label.setStyleSheet(f"color:{_MUTED}; font-size:12px;")
        preset_layout.addWidget(self._size_label)
        layout.addWidget(preset_card)

        layout.addStretch()

        btn_compress = QPushButton("Compress PDF")
        btn_compress.setObjectName("Primary")
        btn_compress.clicked.connect(self._compress)
        layout.addWidget(btn_compress)

    def _browse(self):
        path = self.open_file_dialog("Select a PDF", "PDF (*.pdf)")
        if path:
            self._file_input.setText(path)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self._size_label.setText(f"Current size: {size_mb:.2f} MB")

    def _compress(self):
        src = self._file_input.text().strip()
        if not src:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")
            return

        garbage, deflate, clean, deflate_images, deflate_fonts = \
            _PRESETS[self._preset_combo.currentText()]

        default_path = os.path.join(
            os.path.dirname(src),
            os.path.splitext(os.path.basename(src))[0] + "_compressed.pdf"
        )
        dest = self.save_dialog("Save Compressed PDF", default_path, "PDF (*.pdf)")
        if not dest:
            return

        orig_mb = os.path.getsize(src) / (1024 * 1024)

        def _run():
            doc = fitz.open(src)
            opts = dict(garbage=garbage, deflate=deflate, clean=clean)
            try:
                doc.save(dest, **opts, deflate_images=deflate_images, deflate_fonts=deflate_fonts)
            except TypeError:           # PyMuPDF < 1.18 fallback
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
                new_mb = os.path.getsize(dest) / (1024 * 1024)
                pct    = max(0.0, (orig_mb - new_mb) / orig_mb * 100) if orig_mb else 0
                QMessageBox.information(
                    self, "Done",
                    f"Compressed successfully!\n\n"
                    f"{orig_mb:.2f} MB  →  {new_mb:.2f} MB  ({pct:.0f}% saved)"
                )
            else:
                QMessageBox.critical(self, "Error", msg)

        worker.finished.connect(lambda: _done(True, ""))
        worker.error.connect(lambda m: _done(False, m))
        worker.start()
        dialog.exec()
