import sys
import os

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QButtonGroup, QFrame
)
from PySide6.QtGui import QIcon

from features.merge_feature import MergeFeature
from features.delete_pages_feature import DeletePagesFeature
from features.compress_pdf_feature import CompressPdfFeature
from features.split_pdf_feature import SplitPdfFeature
from features.pdf_to_word_feature import PdfToWordFeature
from features.md_to_pdf_feature import MdToPdfFeature
from features.pdf_to_md_feature import PdfToMdFeature
from features.video_downloader_feature import VideoDownloaderFeature

# ── Theme ──────────────────────────────────────────────────────────────────────
PRIMARY_BG    = "#0E0E0E"
SECONDARY_BG  = "#1C1C1E"
ACCENT_COLOR  = "#00f6ff"
TEXT_COLOR    = "#ffffff"

# ── Register features here to add new ones ─────────────────────────────────────
FEATURES = [
    MergeFeature,
    DeletePagesFeature,
    CompressPdfFeature,
    SplitPdfFeature,
    PdfToWordFeature,
    MdToPdfFeature,
    PdfToMdFeature,
    VideoDownloaderFeature,
]


class FckSaaSApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FckSaaS")
        self.setMinimumSize(1000, 700)

        icon_path = os.path.join(os.path.dirname(__file__), "icon_autopdf.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_ui()
        self._apply_styles()

        if self._nav_group.buttons():
            self._nav_group.buttons()[0].setChecked(True)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setObjectName("Sidebar")
        side_layout = QVBoxLayout(sidebar)

        title = QLabel("FckSaaS")
        title.setObjectName("Brand")
        side_layout.addWidget(title)
        side_layout.addSpacing(30)

        self._nav_group = QButtonGroup(self)
        self._stack = QStackedWidget()

        for index, FeatureClass in enumerate(FEATURES):
            feature = FeatureClass()

            btn = QPushButton(feature.NAV_NAME)
            btn.setCheckable(True)
            self._nav_group.addButton(btn, index)
            side_layout.addWidget(btn)

            self._stack.addWidget(feature)

        side_layout.addStretch()
        layout.addWidget(sidebar)
        layout.addWidget(self._stack)

        self._nav_group.idClicked.connect(self._stack.setCurrentIndex)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {PRIMARY_BG}; color: {TEXT_COLOR}; font-family: 'Segoe UI', sans-serif; }}
            QFrame#Sidebar {{ background-color: {SECONDARY_BG}; border-right: 1px solid #333; }}
            QLabel#Brand {{ font-size: 22px; font-weight: bold; color: {ACCENT_COLOR}; padding: 10px; margin-top: 10px; }}
            QPushButton {{ background: transparent; border: none; padding: 15px; text-align: left; font-size: 14px; border-radius: 5px; }}
            QPushButton:hover {{ background: #333; }}
            QPushButton:checked {{ background: #004545; color: {ACCENT_COLOR}; font-weight: bold; }}
            QPushButton#Primary {{ background-color: {ACCENT_COLOR}; color: black; font-weight: bold; padding: 15px; border-radius: 10px; font-size: 16px; margin-top: 10px; }}
            QPushButton#Primary:hover {{ background-color: #00d6dd; }}
            QLineEdit {{ background: {SECONDARY_BG}; border: 1px solid #444; padding: 10px; border-radius: 5px; color: white; }}
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FckSaaSApp()
    window.show()
    sys.exit(app.exec())
