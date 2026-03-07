from PySide6.QtCore import QThread, Signal


class ConversionWorker(QThread):
    finished = Signal()
    error = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self._fn()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
