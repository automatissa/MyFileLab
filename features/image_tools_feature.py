import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton,
    QLabel, QLineEdit, QFrame, QGridLayout, QScrollArea,
    QWidget, QMessageBox, QComboBox, QSlider, QSizePolicy
)

from .base_feature import BaseFeature, AppCard

_ACCENT   = "#00f6ff"
_BG_CARD  = "#2a2a2c"
_BG_INPUT = "#1C1C1E"
_BORDER   = "#444"
_MUTED    = "#888"

_COLOR_ENHANCE = "#7C3AED"
_COLOR_EXPORT  = "#B45309"

_IMG_FILTER = "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif)"


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _input_card(label="Image File", placeholder="Select an image…"):
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
    btn.setStyleSheet(
        "background:#333; color:white; border-radius:6px; padding:10px; border:none;"
    )
    row.addWidget(btn)
    cl.addLayout(row)

    return card, inp, btn


def _preview_widget():
    """Returns a QLabel sized for image previews."""
    lbl = QLabel("No image selected")
    lbl.setFixedHeight(160)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
        f"border-radius:8px; color:{_MUTED}; font-size:13px;"
    )
    return lbl


def _load_preview(label: QLabel, path: str):
    pix = QPixmap(path)
    if not pix.isNull():
        label.setPixmap(
            pix.scaled(label.width() or 400, label.height(),
                       Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
        )
    else:
        label.setText(os.path.basename(path))


def _slider_row(label: str, min_val=50, max_val=200, default=100):
    """Returns (QFrame, QSlider, value_label).  Values map to x/100 multiplier."""
    frame = QFrame()
    frame.setStyleSheet("background:transparent;")
    row = QHBoxLayout(frame)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(12)

    lbl = QLabel(label)
    lbl.setFixedWidth(100)
    lbl.setStyleSheet(f"color:white; background:transparent; font-size:13px;")
    row.addWidget(lbl)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(min_val, max_val)
    slider.setValue(default)
    slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            height: 4px; background: #444; border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 16px; height: 16px; margin: -6px 0;
            background: {_ACCENT}; border-radius: 8px;
        }}
        QSlider::sub-page:horizontal {{
            background: {_ACCENT}; border-radius: 2px;
        }}
    """)
    row.addWidget(slider)

    val_lbl = QLabel(f"{default / 100:.1f}x")
    val_lbl.setFixedWidth(40)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
    val_lbl.setStyleSheet(f"color:{_ACCENT}; background:transparent; font-size:13px;")
    slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v / 100:.1f}x"))
    row.addWidget(val_lbl)

    return frame, slider, val_lbl


# ══════════════════════════════════════════════════════════════════════════════
#  PANELS
# ══════════════════════════════════════════════════════════════════════════════

class _EnhancePanel(BaseFeature):
    NAV_NAME = ""

    def __init__(self):
        super().__init__()
        self._source_img = None   # PIL Image thumbnail for live preview
        self._src_path   = ""
        self._debounce   = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(120)
        self._debounce.timeout.connect(self._update_preview)
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT — controls ───────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(320)
        left.setStyleSheet(f"background:#1a1a1c; border-right:1px solid #2a2a2c;")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(28, 28, 28, 28)
        lv.setSpacing(20)

        lv.addWidget(QLabel("<h2>Enhance</h2>"))

        # File input
        file_card, self._inp, browse_btn = _input_card()
        browse_btn.clicked.connect(self._browse)
        lv.addWidget(file_card)

        # Sliders card
        sliders_card = QFrame()
        sliders_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        sc = QVBoxLayout(sliders_card)
        sc.setContentsMargins(16, 16, 16, 16)
        sc.setSpacing(16)

        for label, attr in [
            ("Brightness", "_s_brightness"),
            ("Contrast",   "_s_contrast"),
            ("Sharpness",  "_s_sharpness"),
            ("Color",      "_s_color"),
        ]:
            frame, slider, _ = _slider_row(label)
            setattr(self, attr, slider)
            slider.valueChanged.connect(self._debounce.start)
            sc.addWidget(frame)

        lv.addWidget(sliders_card)
        lv.addStretch()
        lv.addWidget(self.primary_button("Save Enhanced Image", self._run))

        root.addWidget(left)

        # ── RIGHT — live preview ──────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("background:#111113;")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)

        self._preview = QLabel("Select an image to preview")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setStyleSheet(f"color:{_MUTED}; font-size:14px; background:transparent;")
        self._preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        rv.addWidget(self._preview)

        root.addWidget(right, stretch=1)

    def _browse(self):
        from PIL import Image
        path = self.open_file_dialog("Select an Image", _IMG_FILTER)
        if not path:
            return
        self._src_path = path
        self._inp.setText(path)
        # Build thumbnail for fast live preview (max 900px on longest side)
        img = Image.open(path).convert("RGB")
        img.thumbnail((900, 900), Image.Resampling.LANCZOS)
        self._source_img = img
        self._update_preview()

    def _update_preview(self):
        if self._source_img is None:
            return
        from PIL import Image, ImageEnhance
        img = self._source_img.copy()
        img = ImageEnhance.Brightness(img).enhance(self._s_brightness.value() / 100)
        img = ImageEnhance.Contrast(img).enhance(self._s_contrast.value()     / 100)
        img = ImageEnhance.Sharpness(img).enhance(self._s_sharpness.value()   / 100)
        img = ImageEnhance.Color(img).enhance(self._s_color.value()           / 100)
        # Convert PIL → QPixmap
        data = img.tobytes("raw", "RGB")
        qimg = QImage(data, img.width, img.height, img.width * 3,
                      QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        w = self._preview.width()  or 800
        h = self._preview.height() or 600
        self._preview.setPixmap(
            pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_preview()

    def _run(self):
        from PIL import Image, ImageEnhance

        if not self._src_path:
            QMessageBox.warning(self, "Warning", "Please select an image.")
            return

        b  = self._s_brightness.value() / 100
        c  = self._s_contrast.value()   / 100
        sh = self._s_sharpness.value()  / 100
        co = self._s_color.value()      / 100

        ext  = os.path.splitext(self._src_path)[1]
        base = os.path.splitext(self._src_path)[0]
        out  = self.save_dialog("Save As", base + "_enhanced" + ext, f"Image (*{ext})")
        if not out:
            return

        src = self._src_path

        def do_work():
            img = Image.open(src).convert("RGB")
            img = ImageEnhance.Brightness(img).enhance(b)
            img = ImageEnhance.Contrast(img).enhance(c)
            img = ImageEnhance.Sharpness(img).enhance(sh)
            img = ImageEnhance.Color(img).enhance(co)
            save_fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG",
                        "webp": "WEBP", "bmp": "BMP"}.get(
                ext.lstrip(".").lower(), "PNG"
            )
            kw = {"quality": 95, "optimize": True} if save_fmt == "JPEG" else {}
            img.save(out, save_fmt, **kw)

        self.run_with_dialog(do_work, f"Saved → {os.path.basename(out)}")


class _ExportPanel(BaseFeature):
    NAV_NAME = ""

    def __init__(self):
        super().__init__()
        self._files = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        layout.addWidget(QLabel("<h1>Batch Export</h1>"))
        layout.addWidget(QLabel(
            "Convert multiple images to a target format with quality control."
        ))

        # File selection
        file_card = QFrame()
        file_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        fc = QVBoxLayout(file_card)
        fc.setContentsMargins(16, 14, 16, 14)
        fc.setSpacing(10)
        fc.addWidget(QLabel("Images"))

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add Images")
        self._add_btn.setStyleSheet(
            "background:#333; color:white; border-radius:6px; padding:10px; border:none;"
        )
        self._add_btn.clicked.connect(self._add_files)
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setStyleSheet(
            "background:#3a1a1a; color:#ff6b6b; border-radius:6px; padding:10px; border:none;"
        )
        self._clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch()
        fc.addLayout(btn_row)

        self._count_lbl = QLabel("No files selected")
        self._count_lbl.setStyleSheet(f"color:{_MUTED}; font-size:12px; background:transparent;")
        fc.addWidget(self._count_lbl)
        layout.addWidget(file_card)

        # Options
        opts = QFrame()
        opts.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        oc = QVBoxLayout(opts)
        oc.setContentsMargins(16, 14, 16, 14)
        oc.setSpacing(12)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Target Format"))
        self._fmt = QComboBox()
        self._fmt.addItems(["JPEG", "PNG", "WebP", "BMP"])
        self._fmt.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; padding:8px; border-radius:6px; color:white;"
        )
        self._fmt.currentTextChanged.connect(self._on_fmt_changed)
        fmt_row.addWidget(self._fmt)
        fmt_row.addStretch()
        oc.addLayout(fmt_row)

        # Quality slider (JPEG / WebP only)
        self._quality_frame, self._quality_slider, self._quality_lbl = _slider_row(
            "Quality", min_val=10, max_val=100, default=90
        )
        self._quality_slider.valueChanged.connect(
            lambda v: self._quality_lbl.setText(f"{v}%")
        )
        self._quality_lbl.setText("90%")
        oc.addWidget(self._quality_frame)
        layout.addWidget(opts)

        layout.addStretch()
        layout.addWidget(self.primary_button("Export All", self._run))

    def _on_fmt_changed(self, fmt: str):
        self._quality_frame.setVisible(fmt in ("JPEG", "WebP"))

    def _add_files(self):
        paths = self.open_files_dialog("Select Images", _IMG_FILTER)
        self._files.extend(p for p in paths if p not in self._files)
        self._count_lbl.setText(
            f"{len(self._files)} file{'s' if len(self._files) != 1 else ''} selected"
        )

    def _clear(self):
        self._files.clear()
        self._count_lbl.setText("No files selected")

    def _run(self):
        from PIL import Image

        if not self._files:
            QMessageBox.warning(self, "Warning", "Please add at least one image.")
            return
        out_dir = self.folder_dialog("Select Output Folder")
        if not out_dir:
            return

        fmt = self._fmt.currentText()
        quality = self._quality_slider.value()
        ext_map = {"JPEG": ".jpg", "PNG": ".png", "WebP": ".webp", "BMP": ".bmp"}
        pil_fmt = {"JPEG": "JPEG", "PNG": "PNG", "WebP": "WEBP", "BMP": "BMP"}
        ext = ext_map[fmt]
        files = list(self._files)

        def do_work():
            for path in files:
                img = Image.open(path).convert("RGB")
                stem = os.path.splitext(os.path.basename(path))[0]
                dest = os.path.join(out_dir, stem + ext)
                kw = {"quality": quality, "optimize": True} if fmt in ("JPEG", "WebP") else {}
                img.save(dest, pil_fmt[fmt], **kw)

        self.run_with_dialog(do_work,
            f"Exported {len(files)} image{'s' if len(files) != 1 else ''} to:\n{out_dir}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN FEATURE
# ══════════════════════════════════════════════════════════════════════════════

class ImageToolsFeature(BaseFeature):
    NAV_NAME = "Images"

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._stack.addWidget(self._build_launcher())   # index 0

        for panel in [_EnhancePanel(), _ExportPanel()]:
            self._stack.addWidget(self._wrap(panel))    # index 1-2

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
        btn = QPushButton("← Back to Images")
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

        layout.addWidget(QLabel("<h1>Images</h1>"))
        layout.addWidget(QLabel("Select a tool to get started."))

        grid = QGridLayout()
        grid.setSpacing(16)
        for col in range(3):
            grid.setColumnStretch(col, 1)

        cards = [
            AppCard("✦",   _COLOR_ENHANCE, "Enhance",
                "Adjust brightness, contrast, sharpness and colour with presets.",
                lambda: self._stack.setCurrentIndex(1)),
            AppCard("EXP", _COLOR_EXPORT,  "Batch Export",
                "Convert multiple images to JPEG, PNG, WebP or BMP.",
                lambda: self._stack.setCurrentIndex(2)),
        ]

        for i, card in enumerate(cards):
            grid.addWidget(card, 0, i)

        layout.addLayout(grid)
        layout.addStretch()
        return scroll
