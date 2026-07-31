import os
import shutil
import tempfile
import zipfile

from lxml import etree
from pypdf import PdfReader, PdfWriter
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFrame, QScrollArea,
    QWidget, QCheckBox, QSizePolicy, QMessageBox
)

from .base_feature import BaseFeature

_ACCENT   = "#00f6ff"
_BG_CARD  = "#2a2a2c"
_BG_INPUT = "#1C1C1E"
_BORDER   = "#444"
_MUTED    = "#888"

_FIELD_LABEL_WIDTH = 150
_CHK_COL_WIDTH     = 28
_HEADER_BG         = "#1A1A1C"


# ══════════════════════════════════════════════════════════════════════════════
#  FIELD DEFINITIONS — ordered, with format-specific keys
# ══════════════════════════════════════════════════════════════════════════════

_FIELD_DEFS = [
    ("title",          "Title"),
    ("author",         "Author"),
    ("subject",        "Subject"),
    ("keywords",       "Keywords"),
    ("creator",        "Creator"),
    ("producer",       "Producer"),
    ("created",        "Created"),
    ("modified",       "Modified"),
    ("description",    "Description"),
    ("last_mod_by",    "Last Modified By"),
    ("revision",       "Revision"),
    ("category",       "Category"),
    ("company",        "Company"),
    ("manager",        "Manager"),
    ("application",    "Application"),
    ("app_version",    "App Version"),
    ("template",       "Template"),
    ("pages",          "Pages"),
    ("words",          "Words"),
    ("characters",     "Characters"),
    ("lines",          "Lines"),
    ("paragraphs",     "Paragraphs"),
    ("total_time",     "Total Time (min)"),
    ("image_make",     "Camera Make"),
    ("image_model",    "Camera Model"),
    ("image_sw",       "Software"),
    ("image_copyright","Copyright"),
    ("image_dt",       "Date Taken"),
    ("image_artist",   "Artist"),
]


# ── PDF ────────────────────────────────────────────────────────────────────────

_PDF_KEY_MAP = {
    "title":       "/Title",
    "author":      "/Author",
    "subject":     "/Subject",
    "keywords":    "/Keywords",
    "creator":     "/Creator",
    "producer":    "/Producer",
    "created":     "/CreationDate",
    "modified":    "/ModDate",
}


def _read_pdf_metadata(path: str) -> dict:
    reader = PdfReader(path)
    meta = reader.metadata or {}
    result = {}
    for field_key, pdf_key in _PDF_KEY_MAP.items():
        val = meta.get(pdf_key)
        result[field_key] = str(val).strip() if val else None
    return result


def _write_pdf_metadata(path: str, metadata: dict) -> None:
    reader = PdfReader(path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.clone_reader_document_root(reader)

    pdf_meta = dict(reader.metadata or {})
    for field_key, pdf_key in _PDF_KEY_MAP.items():
        val = metadata.get(field_key)
        if val is not None:
            pdf_meta[pdf_key] = val

    writer.add_metadata(pdf_meta)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(tmp_fd)
    try:
        with open(tmp_path, "wb") as f:
            writer.write(f)
        shutil.move(tmp_path, path)
    finally:
        writer.close()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── OOXML (DOCX / XLSX / PPTX) ─────────────────────────────────────────────────

_NS_CORE    = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
_NS_DC      = "http://purl.org/dc/elements/1.1/"
_NS_DCTERMS = "http://purl.org/dc/terms/"
_NS_XSI     = "http://www.w3.org/2001/XMLSchema-instance"
_NS_APP     = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"

_CORE_MAP = [
    ("title",        "dc:title",        _NS_DC),
    ("author",       "dc:creator",       _NS_DC),
    ("subject",      "dc:subject",       _NS_DC),
    ("description",  "dc:description",   _NS_DC),
    ("last_mod_by",  "cp:lastModifiedBy", _NS_CORE),
    ("keywords",     "cp:keywords",      _NS_CORE),
    ("category",     "cp:category",      _NS_CORE),
    ("revision",     "cp:revision",      _NS_CORE),
    ("created",      "dcterms:created",  _NS_DCTERMS),
    ("modified",     "dcterms:modified", _NS_DCTERMS),
]

_CORE_MAP_DICT = {key: (local_name, ns_uri) for key, local_name, ns_uri in _CORE_MAP}

_APP_MAP = [
    ("application", "Application"),
    ("app_version", "AppVersion"),
    ("template",    "Template"),
    ("company",     "Company"),
    ("manager",     "Manager"),
    ("pages",       "Pages"),
    ("words",       "Words"),
    ("characters",  "Characters"),
    ("lines",       "Lines"),
    ("paragraphs",  "Paragraphs"),
    ("total_time",  "TotalTime"),
]

_APP_MAP_DICT = {key: tag for key, tag in _APP_MAP}


def _read_ooxml_metadata(path: str) -> dict:
    result = {}
    with zipfile.ZipFile(path, "r") as z:
        if "docProps/core.xml" in z.namelist():
            with z.open("docProps/core.xml") as f:
                tree = etree.parse(f)
                root = tree.getroot()
                for field_key, local_name, ns_uri in _CORE_MAP:
                    el = root.find(f"{{{ns_uri}}}{local_name.split(':', 1)[-1]}" if ":" in local_name else local_name)
                    result[field_key] = el.text if el is not None and el.text else None

        if "docProps/app.xml" in z.namelist():
            with z.open("docProps/app.xml") as f:
                tree = etree.parse(f)
                root = tree.getroot()
                for field_key, tag in _APP_MAP:
                    el = root.find(f"{{{_NS_APP}}}{tag}")
                    result[field_key] = el.text if el is not None and el.text else None

    return result


def _write_ooxml_metadata(path: str, metadata: dict) -> None:
    core_fields = {fk for fk, _, _ in _CORE_MAP}
    app_fields  = {fk for fk, _ in _APP_MAP}
    changes_core = {k: v for k, v in metadata.items() if k in core_fields}
    changes_app  = {k: v for k, v in metadata.items() if k in app_fields}

    tmp_fd, tmp_path = tempfile.mkstemp()
    os.close(tmp_fd)

    try:
        with zipfile.ZipFile(path, "r") as zin:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)

                    if item.filename == "docProps/core.xml" and changes_core:
                        tree = etree.fromstring(data)
                        root = tree
                        for field_key, new_val in changes_core.items():
                            local_name, ns_uri = _CORE_MAP_DICT[field_key]
                            tag_name = local_name.split(":", 1)[-1]
                            el = root.find(f"{{{ns_uri}}}{tag_name}")
                            if new_val is not None:
                                if el is None:
                                    el = etree.SubElement(root, f"{{{ns_uri}}}{tag_name}")
                                el.text = str(new_val)
                            else:
                                if el is not None:
                                    root.remove(el)
                        data = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

                    elif item.filename == "docProps/app.xml" and changes_app:
                        tree = etree.fromstring(data)
                        root = tree
                        for field_key, new_val in changes_app.items():
                            tag = _APP_MAP_DICT[field_key]
                            el = root.find(f"{{{_NS_APP}}}{tag}")
                            if new_val is not None:
                                if el is None:
                                    el = etree.SubElement(root, f"{{{_NS_APP}}}{tag}")
                                el.text = str(new_val)
                            else:
                                if el is not None:
                                    root.remove(el)
                        data = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

                    zout.writestr(item, data)

        shutil.move(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Images (EXIF read-only) ────────────────────────────────────────────────────

_EXIF_TAG_MAP = {
    0x010F: "image_make",
    0x0110: "image_model",
    0x0131: "image_sw",
    0x013B: "image_artist",
    0x8298: "image_copyright",
    0x010E: "description",
    0x9003: "image_dt",
    0x9C9B: "title",
    0x9C9E: "description",
    0x9C9C: "keywords",
    0x9C9D: "author",
}


def _read_image_metadata(path: str) -> dict:
    img = Image.open(path)
    result = {}
    try:
        exif = img.getexif()
        if exif:
            for tag_id, field_key in _EXIF_TAG_MAP.items():
                val = exif.get(tag_id)
                if val is not None:
                    result[field_key] = str(val).strip()
    except Exception:
        pass
    img.close()
    return result


# ── Unified read ───────────────────────────────────────────────────────────────

_OOXML_EXTS = {".docx", ".xlsx", ".pptx"}


def _read_all_metadata(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _read_pdf_metadata(path)
    elif ext in _OOXML_EXTS:
        return _read_ooxml_metadata(path)
    elif ext in {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp"}:
        return _read_image_metadata(path)
    return {}


def _write_metadata(path: str, metadata: dict) -> None:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        _write_pdf_metadata(path, metadata)
    elif ext in _OOXML_EXTS:
        _write_ooxml_metadata(path, metadata)
    else:
        raise NotImplementedError(f"Writing metadata for {ext} is not yet supported.")


# ══════════════════════════════════════════════════════════════════════════════
#  UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def _make_header_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"background:transparent; color:{_MUTED}; font-size:12px; font-weight:bold; padding:4px 0;")
    return lbl


class _EditRow(QFrame):
    def __init__(self, field_key: str, field_label: str, original_value: str | None, parent=None):
        super().__init__(parent)
        self.field_key = field_key
        self.setStyleSheet(f"background:transparent; border-bottom:1px solid {_BORDER};")
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)

        self._chk = QCheckBox()
        self._chk.setStyleSheet("background:transparent;")
        self._chk.setFixedWidth(_CHK_COL_WIDTH)
        self._chk.toggled.connect(self._on_toggle)
        row.addWidget(self._chk)

        lbl = QLabel(field_label)
        lbl.setFixedWidth(_FIELD_LABEL_WIDTH)
        lbl.setStyleSheet("background:transparent; color:white; font-size:13px; font-weight:bold;")
        row.addWidget(lbl)

        val_lbl = QLabel(original_value or '<span style="color:#666;">(not set)</span>')
        val_lbl.setTextFormat(Qt.TextFormat.RichText)
        val_lbl.setStyleSheet("background:transparent; color:white; font-size:13px;")
        val_lbl.setWordWrap(True)
        row.addWidget(val_lbl, 1)

        self._input = QLineEdit()
        self._input.setText(original_value or "")
        self._input.setPlaceholderText("edit\u2026")
        self._input.setEnabled(False)
        self._input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:8px; border-radius:5px; color:#666;"
        )
        row.addWidget(self._input, 1)

        if original_value:
            self._chk.setChecked(True)

    def _on_toggle(self, checked):
        self._input.setEnabled(checked)
        if checked:
            self._input.setStyleSheet(
                f"background:{_BG_INPUT}; border:1px solid {_ACCENT}; "
                f"padding:8px; border-radius:5px; color:white;"
            )
        else:
            self._input.setStyleSheet(
                f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
                f"padding:8px; border-radius:5px; color:#666;"
            )

    def is_checked(self) -> bool:
        return self._chk.isChecked()

    def value(self) -> str | None:
        if not self._chk.isChecked():
            return None
        text = self._input.text().strip()
        return text if text else None

    def reset(self):
        self._chk.setChecked(False)
        self._input.clear()
        self._input.setEnabled(False)
        self._input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:8px; border-radius:5px; color:#666;"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN FEATURE
# ══════════════════════════════════════════════════════════════════════════════

class MetadataEditorFeature(BaseFeature):
    NAV_NAME = "Metadata Editor"

    _SUPPORTED_FILTER = (
        "All Supported (*.pdf *.docx *.xlsx *.pptx *.jpg *.jpeg *.png *.webp *.tiff *.tif *.bmp);;"
        "PDF (*.pdf);;Word (*.docx);;Excel (*.xlsx);;PowerPoint (*.pptx);;"
        "Images (*.jpg *.jpeg *.png *.webp *.tiff *.tif *.bmp)"
    )

    def __init__(self):
        super().__init__()
        self._edit_rows: dict[str, _EditRow] = {}
        self._current_path: str | None = None
        self._current_ext: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top file selector ──────────────────────────────────────────────────
        top_card = QFrame()
        top_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        tc = QVBoxLayout(top_card)
        tc.setContentsMargins(16, 14, 16, 14)
        tc.setSpacing(10)
        tc.addWidget(QLabel("Select a document or image"))

        file_row = QHBoxLayout()
        self._file_input = QLineEdit()
        self._file_input.setPlaceholderText("Select a file to inspect its metadata…")
        self._file_input.setReadOnly(True)
        self._file_input.setStyleSheet(
            f"background:{_BG_INPUT}; border:1px solid {_BORDER}; "
            f"padding:10px; border-radius:6px; color:white;"
        )
        file_row.addWidget(self._file_input)

        btn_browse = QPushButton("Browse")
        btn_browse.setFixedWidth(100)
        btn_browse.setStyleSheet(
            "background:#333; color:white; border-radius:6px; padding:10px; border:none;"
        )
        btn_browse.clicked.connect(self._browse_file)
        file_row.addWidget(btn_browse)

        tc.addLayout(file_row)
        tc.addStretch()

        top_wrapper = QWidget()
        top_wrapper.setStyleSheet("background:transparent;")
        twl = QVBoxLayout(top_wrapper)
        twl.setContentsMargins(40, 28, 40, 0)
        twl.addWidget(QLabel("<h1>Metadata Editor</h1>"))
        twl.addSpacing(6)
        twl.addWidget(QLabel(
            "View and modify document metadata. Check the fields you want to change, "
            "edit their values, and click Apply. Unchecked fields are left untouched."
        ))
        twl.addSpacing(8)
        twl.addWidget(top_card)
        root.addWidget(top_wrapper)

        # ── Body: table scroll area ──────────────────────────────────────────────
        body_scroll = QScrollArea()
        body_scroll.setWidgetResizable(True)
        body_scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        body_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        table_card = QFrame()
        table_card.setStyleSheet(f"background:{_BG_CARD}; border-radius:10px;")
        table_inner = QVBoxLayout(table_card)
        table_inner.setContentsMargins(0, 0, 0, 0)
        table_inner.setSpacing(0)

        header_widget = QWidget()
        header_widget.setStyleSheet(f"background:{_HEADER_BG}; border-radius:10px;")
        header_row = QHBoxLayout(header_widget)
        header_row.setContentsMargins(12, 12, 12, 12)
        header_row.setSpacing(10)

        hdr_spacer = QWidget()
        hdr_spacer.setFixedWidth(_CHK_COL_WIDTH)
        hdr_spacer.setStyleSheet("background:transparent;")
        header_row.addWidget(hdr_spacer)

        hdr_field = QWidget()
        hdr_field.setFixedWidth(_FIELD_LABEL_WIDTH)
        hdr_field.setStyleSheet("background:transparent;")
        hdr_fl = QVBoxLayout(hdr_field)
        hdr_fl.setContentsMargins(0, 0, 0, 0)
        hdr_fl.addWidget(_make_header_label("Field"))
        header_row.addWidget(hdr_field)

        hdr_current = _make_header_label("Current Value")
        header_row.addWidget(hdr_current, 1)
        hdr_edit = _make_header_label("Edit Value")
        header_row.addWidget(hdr_edit, 1)

        table_inner.addWidget(header_widget)

        self._rows_list = QVBoxLayout()
        self._rows_list.setSpacing(0)
        self._rows_list.setContentsMargins(0, 0, 0, 0)
        table_inner.addLayout(self._rows_list)

        table_wrapper = QWidget()
        table_wrapper.setStyleSheet("background:transparent;")
        twl = QVBoxLayout(table_wrapper)
        twl.setContentsMargins(40, 16, 40, 16)
        twl.addWidget(table_card)

        body_scroll.setWidget(table_wrapper)
        root.addWidget(body_scroll)

        # ── Bottom: Apply button ───────────────────────────────────────────────
        bottom_wrapper = QWidget()
        bottom_wrapper.setStyleSheet("background:transparent;")
        bwl = QVBoxLayout(bottom_wrapper)
        bwl.setContentsMargins(40, 8, 40, 24)

        apply_btn = self.primary_button("Apply Metadata Changes", self._apply)
        apply_btn.setEnabled(False)
        self._apply_btn = apply_btn
        bwl.addWidget(apply_btn)
        root.addWidget(bottom_wrapper)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _browse_file(self):
        path = self.open_file_dialog("Select a File", self._SUPPORTED_FILTER)
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str):
        self._current_path = path
        self._current_ext = os.path.splitext(path)[1].lower()
        self._file_input.setText(path)

        try:
            metadata = _read_all_metadata(path)
        except Exception as e:
            QMessageBox.warning(self, "Read Error", f"Could not read metadata:\n{e}")
            return

        self._clear_rows()

        for field_key, field_label in _FIELD_DEFS:
            orig = metadata.get(field_key)

            row = _EditRow(field_key, field_label, orig)
            self._edit_rows[field_key] = row
            self._rows_list.addWidget(row)

        self._rows_list.addStretch()

        can_write = self._current_ext in {".pdf"} or self._current_ext in _OOXML_EXTS
        self._apply_btn.setEnabled(can_write)
        if not can_write:
            self._apply_btn.setText("Image metadata writing coming soon")
            self._apply_btn.setStyleSheet(
                f"background:{_BG_INPUT}; color:{_MUTED}; font-weight:bold; "
                f"padding:15px; border-radius:10px; font-size:16px; margin-top:10px; border:none;"
            )

    def _apply(self):
        if not self._current_path:
            return

        metadata_to_write = {}
        for field_key, row in self._edit_rows.items():
            val = row.value()
            if val is not None:
                metadata_to_write[field_key] = val

        if not metadata_to_write:
            QMessageBox.information(self, "No Changes", "No fields are checked for modification.")
            return

        def do_work():
            _write_metadata(self._current_path, metadata_to_write)

        self.run_with_dialog(do_work, "Metadata updated successfully!")

        self._load_file(self._current_path)

    def _clear_rows(self):
        def _clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.deleteLater()
                elif item.layout():
                    _clear_layout(item.layout())

        _clear_layout(self._rows_list)
        self._edit_rows.clear()

        self._apply_btn.setText("Apply Metadata Changes")
        self._apply_btn.setStyleSheet(
            f"background-color:{_ACCENT}; color:black; font-weight:bold; "
            f"padding:15px; border-radius:10px; font-size:16px; margin-top:10px;"
        )
