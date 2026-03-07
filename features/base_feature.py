from PySide6.QtWidgets import QWidget, QMessageBox

from .worker import ConversionWorker
from .processing_dialog import ProcessingDialog


class BaseFeature(QWidget):
    """
    Base class for all features.
    Each subclass must define NAV_NAME (sidebar label) and implement _setup_ui().
    """
    NAV_NAME: str = "Feature"

    def __init__(self):
        super().__init__()

    def run_with_dialog(self, fn, success_msg: str):
        """Run fn in a background thread behind an animated processing dialog."""
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
