import importlib
import sys
import os


def _resource(relative: str) -> str:
    """Resolve a resource path — works both in dev and PyInstaller frozen exe."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QButtonGroup, QFrame
)
from PySide6.QtGui import QIcon

# ── Theme ──────────────────────────────────────────────────────────────────────
PRIMARY_BG    = "#0E0E0E"
SECONDARY_BG  = "#1C1C1E"
ACCENT_COLOR  = "#00f6ff"
TEXT_COLOR    = "#ffffff"

# ── Feature registry (module_path, class_name, nav_name) ───────────────────────
def _create_feature(module_path: str, cls_name: str):
    mod = importlib.import_module(module_path)
    cls = getattr(mod, cls_name)
    return cls()

_FEATURE_SPECS = [
    ("features.pdf_tools_feature", "PdfToolsFeature", "PDF Tools"),
    ("features.pdf_export_feature", "PdfExportFeature", "Converter"),
    ("features.image_tools_feature", "ImageToolsFeature", "Images"),
    ("features.video_downloader_feature", "VideoDownloaderFeature", "Media Downloader"),
    ("features.metadata_feature", "MetadataEditorFeature", "Metadata Editor"),
]

_LEGAL_SPECS = [
    ("features.legal_feature", "LicenseFeature", "License"),
    ("features.legal_feature", "TermsOfUseFeature", "Terms of Use"),
]


class MyFileLabApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyFileLab")
        self.setMinimumSize(1000, 700)

        icon_path = _resource("icon_autopdf.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)

        self._setup_ui()
        self._apply_styles()

        if self._nav_group.buttons():
            self._nav_group.buttons()[0].setChecked(True)

        # Defer heavy imports to after the window is painted
        QTimer.singleShot(10, self._load_deferred_features)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setObjectName("Sidebar")
        side_layout = QVBoxLayout(sidebar)

        title = QLabel("MyFileLab")
        title.setObjectName("Brand")
        side_layout.addWidget(title)
        side_layout.addSpacing(30)

        self._nav_group = QButtonGroup(self)
        self._stack = QStackedWidget()

        # ── Create first feature immediately (the visible one) ────────────────
        mod_path, cls_name, nav_name = _FEATURE_SPECS[0]
        feature = _create_feature(mod_path, cls_name)
        btn = QPushButton(nav_name)
        btn.setCheckable(True)
        self._nav_group.addButton(btn, 0)
        side_layout.addWidget(btn)
        self._stack.addWidget(feature)

        # ── Placeholders for remaining functional features ────────────────────
        for index, (_, _, nav_name) in enumerate(_FEATURE_SPECS[1:], start=1):
            btn = QPushButton(nav_name)
            btn.setCheckable(True)
            self._nav_group.addButton(btn, index)
            side_layout.addWidget(btn)

            placeholder = QLabel("")
            self._stack.addWidget(placeholder)

        # ── Separator ─────────────────────────────────────────────────────────
        side_layout.addSpacing(12)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#3a3a3c; max-height:1px; margin:0 14px; border:none;")
        side_layout.addWidget(sep)
        side_layout.addSpacing(4)

        # ── Legal feature buttons + placeholders ──────────────────────────────
        self._legal_start_idx = len(_FEATURE_SPECS)
        for index, (_, _, nav_name) in enumerate(_LEGAL_SPECS, start=self._legal_start_idx):
            btn = QPushButton(nav_name)
            btn.setCheckable(True)
            btn.setObjectName("LegalNav")
            self._nav_group.addButton(btn, index)
            side_layout.addWidget(btn)

            placeholder = QLabel("")
            self._stack.addWidget(placeholder)

        side_layout.addStretch()

        # ── Footer links ──────────────────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet("border-top: 1px solid #2a2a2c; background: transparent;")
        fl = QVBoxLayout(footer)
        fl.setContentsMargins(14, 10, 14, 14)
        fl.setSpacing(6)

        lbl = QLabel(
            'Built by <a href="https://www.linkedin.com/in/issadiouf/">Issa</a>'
            ' · <a href="https://github.com/automatissa/MyFileLab">GitHub</a>'
        )
        lbl.setOpenExternalLinks(True)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            "color: #555; font-size: 11px; background: transparent; border: none;"
            "a { color: #777; text-decoration: none; }"
        )
        fl.addWidget(lbl)

        side_layout.addWidget(footer)

        layout.addWidget(sidebar)
        layout.addWidget(self._stack)

        self._nav_group.idClicked.connect(self._stack.setCurrentIndex)

    def _load_deferred_features(self):
        for index, (mod_path, cls_name, _) in enumerate(_FEATURE_SPECS[1:], start=1):
            feature = _create_feature(mod_path, cls_name)
            old = self._stack.widget(index)
            self._stack.removeWidget(old)
            old.deleteLater()
            self._stack.insertWidget(index, feature)

        for index, (mod_path, cls_name, _) in enumerate(_LEGAL_SPECS, start=self._legal_start_idx):
            feature = _create_feature(mod_path, cls_name)
            old = self._stack.widget(index)
            self._stack.removeWidget(old)
            old.deleteLater()
            self._stack.insertWidget(index, feature)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {PRIMARY_BG}; color: {TEXT_COLOR}; font-family: 'Segoe UI', sans-serif; }}
            QFrame#Sidebar {{ background-color: {SECONDARY_BG}; border-right: 1px solid #333; }}
            QLabel#Brand {{ font-size: 22px; font-weight: bold; color: {ACCENT_COLOR}; padding: 10px; margin-top: 10px; }}
            QPushButton {{ background: transparent; border: none; padding: 15px; text-align: left; font-size: 14px; border-radius: 5px; }}
            QPushButton:hover {{ background: #333; }}
            QPushButton:checked {{ background: #004545; color: {ACCENT_COLOR}; font-weight: bold; }}
            QPushButton#LegalNav {{ padding: 10px 15px; font-size: 12px; color: #888; }}
            QPushButton#LegalNav:hover {{ background: #2a2a2c; }}
            QPushButton#LegalNav:checked {{ background: #004545; color: {ACCENT_COLOR}; font-weight: bold; }}
            QPushButton#Primary {{ background-color: {ACCENT_COLOR}; color: black; font-weight: bold; padding: 15px; border-radius: 10px; font-size: 16px; margin-top: 10px; }}
            QPushButton#Primary:hover {{ background-color: #00d6dd; }}
            QLineEdit {{ background: {SECONDARY_BG}; border: 1px solid #444; padding: 10px; border-radius: 5px; color: white; }}
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyFileLabApp()
    window.show()
    sys.exit(app.exec())
