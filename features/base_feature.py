import os

from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog

from .worker import ConversionWorker
from .processing_dialog import ProcessingDialog


class BaseFeature(QWidget):
    """
    Base class for all features.

    Each subclass must define NAV_NAME (sidebar label) and implement _setup_ui().

    ── Standard dialog helpers (use these instead of QFileDialog directly) ──────
      self.open_file_dialog(title, file_filter)        → str  (single file)
      self.open_files_dialog(title, file_filter)       → list[str]  (multiple files)
      self.save_dialog(title, default_path, filter)    → str  (save path)

    These helpers always reset to the supplied default path/directory, so the
    dialog never "remembers" a previous selection across invocations.
    """
    NAV_NAME: str = "Feature"

    def __init__(self):
        super().__init__()

    # ── Dialog helpers ─────────────────────────────────────────────────────────

    def open_file_dialog(self, title: str, file_filter: str) -> str:
        """Open a single-file picker. Returns chosen path or empty string."""
        path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        return path

    def open_files_dialog(self, title: str, file_filter: str) -> list:
        """Open a multi-file picker. Returns list of chosen paths (may be empty)."""
        paths, _ = QFileDialog.getOpenFileNames(self, title, "", file_filter)
        return paths

    def folder_dialog(self, title: str) -> str:
        """Open a folder picker. Returns chosen path or empty string."""
        return QFileDialog.getExistingDirectory(self, title)

    def save_dialog(self, title: str, default_path: str, file_filter: str) -> str:
        """
        Open a Save As dialog that always pre-fills default_path, regardless of
        what the user picked last time (bypasses Qt's internal path memory).
        Returns the chosen path, or empty string if cancelled.
        """
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

    # ── Background task helper ─────────────────────────────────────────────────

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
