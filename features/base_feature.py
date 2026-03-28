import os

from PySide6.QtCore import QThread, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QMessageBox, QFileDialog, QPushButton,
    QDialog, QVBoxLayout, QLabel, QProgressBar, QFrame
)


# ── Background worker ─────────────────────────────────────────────────────────

class ConversionWorker(QThread):
    finished = Signal()
    error    = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self._fn()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ── Processing dialog ─────────────────────────────────────────────────────────

_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class ProcessingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setModal(True)
        self.setFixedSize(300, 160)
        self.setStyleSheet("""
            QDialog { background:#1C1C1E; border:1px solid #2a2a2c; border-radius:12px; }
            QLabel#spinner { color:#00f6ff; font-size:32px; }
            QLabel#status  { color:#cccccc; font-size:13px; font-family:'Segoe UI',sans-serif; }
            QProgressBar { border:none; border-radius:3px; background:#2a2a2c;
                           max-height:5px; min-height:5px; }
            QProgressBar::chunk { background:#00f6ff; border-radius:3px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._spinner = QLabel(_SPINNER[0])
        self._spinner.setObjectName("spinner")
        self._spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._spinner)

        status = QLabel("Processing, please wait…")
        status.setObjectName("status")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)

        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setTextVisible(False)
        layout.addWidget(bar)

        self._idx = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(80)

    def _tick(self):
        self._idx = (self._idx + 1) % len(_SPINNER)
        self._spinner.setText(_SPINNER[self._idx])

    def closeEvent(self, event):
        event.ignore()


# ── Base feature ──────────────────────────────────────────────────────────────

class BaseFeature(QWidget):
    NAV_NAME: str = "Feature"

    def __init__(self):
        super().__init__()

    def open_file_dialog(self, title: str, file_filter: str) -> str:
        path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        return path

    def open_files_dialog(self, title: str, file_filter: str) -> list:
        paths, _ = QFileDialog.getOpenFileNames(self, title, "", file_filter)
        return paths

    def folder_dialog(self, title: str) -> str:
        return QFileDialog.getExistingDirectory(self, title)

    def save_dialog(self, title: str, default_path: str, file_filter: str) -> str:
        dialog = QFileDialog(self, title)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter(file_filter)
        directory = os.path.dirname(default_path) or os.path.expanduser("~")
        dialog.setDirectory(directory)
        dialog.selectFile(os.path.basename(default_path))
        if dialog.exec():
            files = dialog.selectedFiles()
            return files[0] if files else ""
        return ""

    def primary_button(self, label: str, on_click) -> QPushButton:
        """Standard primary action button — use this for every main execute button."""
        btn = QPushButton(label)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #00f6ff;
                color: black;
                font-weight: bold;
                font-size: 16px;
                padding: 15px;
                border-radius: 10px;
                border: none;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #00d6dd; }
            QPushButton:disabled { background-color: #2a2a2c; color: #555; border: 1px solid #444; }
        """)
        btn.clicked.connect(on_click)
        return btn

    def run_with_dialog(self, fn, success_msg: str):
        self._worker = ConversionWorker(fn)
        dialog = ProcessingDialog(self)
        _fired = [False]

        def _done(success: bool, msg: str):
            if _fired[0]:
                return
            _fired[0] = True
            dialog.accept()
            if success:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.critical(self, "Error", msg)

        self._worker.finished.connect(lambda: _done(True, success_msg))
        self._worker.error.connect(lambda msg: _done(False, msg))
        self._worker.start()
        dialog.exec()


# ── Shared card component ─────────────────────────────────────────────────────

_C_NORMAL   = "#2a2a2c"
_C_DISABLED = "#1e1e1e"

_CARD_ACTIVE   = f"QFrame {{ background:{_C_NORMAL}; border-radius:18px; border:1px solid #383838; }}"
_CARD_HOVER    =  "QFrame { background: rgba(0,246,255,0.07); border-radius:18px; border:2px solid rgba(0,246,255,0.35); }"
_CARD_DISABLED = f"QFrame {{ background:{_C_DISABLED}; border-radius:18px; border:1px solid #2a2a2a; }}"


class AppCard(QFrame):
    """
    Reusable card that acts as a button.

    letter      — short text shown in the icon bubble
    color       — icon bubble color (hex).  Pass None → coming-soon state.
    title       — bold card title
    description — short body text
    on_click    — callable fired on click.  Pass None → coming-soon state.
    """

    def __init__(self, letter: str, color, title: str, description: str,
                 on_click=None, parent=None):
        super().__init__(parent)
        self._on_click = on_click
        self._active   = on_click is not None
        self.setFixedHeight(180)
        self.setStyleSheet(_CARD_ACTIVE if self._active else _CARD_DISABLED)

        if self._active:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        icon_bg    = (color or "#3a3a3a")
        icon_color = "white" if self._active else "#555"

        icon = QLabel(letter)
        icon.setFixedSize(48, 48)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"background:{icon_bg}; border-radius:12px; color:{icon_color}; "
            f"font-size:18px; font-weight:bold; border:none;"
        )
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignLeft)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            "color:white; font-size:15px; font-weight:bold; "
            "background:transparent; border:none;"
            if self._active else
            "color:#444; font-size:15px; font-weight:bold; "
            "background:transparent; border:none;"
        )
        layout.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(description)
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet(
            "color:#aaaaaa; font-size:12px; background:transparent; border:none;"
            if self._active else
            "color:#3a3a3a; font-size:12px; background:transparent; border:none;"
        )
        layout.addWidget(self._desc_lbl)

        layout.addStretch()

        if not self._active:
            badge = QLabel("Coming Soon")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                "background:#2a2a2a; color:#444; font-size:11px; font-weight:bold; "
                "padding:6px 14px; border-radius:10px; border:none;"
            )
            layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignLeft)

    def enterEvent(self, e):
        if self._active:
            self.setStyleSheet(_CARD_HOVER)
            self._title_lbl.setStyleSheet(
                "color:#00f6ff; font-size:15px; font-weight:bold; "
                "background:transparent; border:none;"
            )
            self._desc_lbl.setStyleSheet(
                "color:#dddddd; font-size:12px; background:transparent; border:none;"
            )
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setStyleSheet(_CARD_ACTIVE if self._active else _CARD_DISABLED)
        if self._active:
            self._title_lbl.setStyleSheet(
                "color:white; font-size:15px; font-weight:bold; "
                "background:transparent; border:none;"
            )
            self._desc_lbl.setStyleSheet(
                "color:#aaaaaa; font-size:12px; background:transparent; border:none;"
            )
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if self._active and self._on_click:
            self._on_click()
        super().mousePressEvent(e)
