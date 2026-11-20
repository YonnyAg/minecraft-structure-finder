"""Qt adapter: one worker thread and a cooperative cancellation flag per search."""

from threading import Event

from PySide6.QtCore import QThread, Signal

from .domain import SearchRequest
from .services import SearchCancelledError, SearchService


class SearchWorker(QThread):
    progress = Signal(int, int)
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal(str)

    def __init__(self, service: SearchService, request: SearchRequest, parent=None):
        super().__init__(parent)
        self.service = service
        self.request = request
        self.stop = Event()

    def cancel(self) -> None:
        self.stop.set()

    def run(self) -> None:
        try:
            results = self.service.search(self.request, progress=self.progress.emit, cancelled=self.stop.is_set)
            self.completed.emit(results)
        except SearchCancelledError as error:
            self.cancelled.emit(str(error))
        except Exception as error:
            self.failed.emit(str(error) or type(error).__name__)
