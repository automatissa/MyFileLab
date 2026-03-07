from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

_STYLE = """
QDialog {
    background-color: #1C1C1E;
    border: 1px solid #2a2a2c;
    border-radius: 12px;
}
QLabel#spinner {
    color: #00f6ff;
    font-size: 32px;
}
QLabel#status {
    color: #cccccc;
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}
QProgressBar {
    border: none;
    border-radius: 3px;
    background: #2a2a2c;
    max-height: 5px;
    min-height: 5px;
}
QProgressBar::chunk {
    background-color: #00f6ff;
    border-radius: 3px;
}
"""


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
        self.setStyleSheet(_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._spinner = QLabel(_SPINNER_FRAMES[0])
        self._spinner.setObjectName("spinner")
        self._spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._spinner)

        self._status = QLabel("Processing, please wait…")
        self._status.setObjectName("status")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setTextVisible(False)
        layout.addWidget(bar)

        self._frame_idx = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(80)

    def _tick(self):
        self._frame_idx = (self._frame_idx + 1) % len(_SPINNER_FRAMES)
        self._spinner.setText(_SPINNER_FRAMES[self._frame_idx])

    def closeEvent(self, event):
        event.ignore()
