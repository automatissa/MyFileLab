import os
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QVBoxLayout, QLabel, QScrollArea

from .base_feature import BaseFeature

_FILE_TO_NAV = {
    "LICENSE": "License",
    "TERMS_OF_USE.md": "Terms of Use",
}


class _LegalViewerBase(BaseFeature):
    _FILENAME: str = ""
    NAV_NAME: str = ""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(16)

        title = QLabel(f"<h1>{self.NAV_NAME}</h1>")
        title.setStyleSheet("background:transparent; border:none;")
        layout.addWidget(title)

        self._label = QLabel()
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setWordWrap(True)
        self._label.setOpenExternalLinks(False)
        self._label.linkActivated.connect(self._on_link_activated)
        self._label.setStyleSheet("""
            QLabel {
                background: #1C1C1E;
                color: #cccccc;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
            }
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setWidget(self._label)
        layout.addWidget(scroll)

    def _on_link_activated(self, link: str):
        if link.startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(link))
            return

        target_nav = _FILE_TO_NAV.get(link)
        if target_nav:
            main_win = self.window()
            if main_win and hasattr(main_win, "_nav_group"):
                for btn in main_win._nav_group.buttons():
                    if btn.text() == target_nav:
                        btn.click()
                        break

    def _load_content(self):
        if getattr(sys, "frozen", False):
            path = os.path.join(sys._MEIPASS, self._FILENAME)
        else:
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self._FILENAME)

        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                raw = f.read()
            import markdown
            html = markdown.markdown(raw, extensions=["extra", "codehilite"])
            html = f"<body style='color:#cccccc; font-family:\"Segoe UI\",sans-serif;'>{html}</body>"
        else:
            html = f"<p style='color:#888;'><i>{self._FILENAME} not found.</i></p>"

        self._label.setText(html)


class LicenseFeature(_LegalViewerBase):
    NAV_NAME = "License"
    _FILENAME = "LICENSE"


class TermsOfUseFeature(_LegalViewerBase):
    NAV_NAME = "Terms of Use"
    _FILENAME = "TERMS_OF_USE.md"
