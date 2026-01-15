import os
from PyQt6.QtWidgets import QTreeWidget
from PyQt6.QtCore import pyqtSignal

class VideoTreeWidget(QTreeWidget):
    files_dropped = pyqtSignal(list)
    
    ACCEPTED_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.wmv', '.mpeg', '.mpg'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.itemAt(event.position().toPoint()):
            self.clearSelection()

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            # Check if any file has valid extension
            has_video = False
            for url in mime.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    ext = os.path.splitext(path)[1].lower()
                    if ext in self.ACCEPTED_EXTENSIONS:
                        has_video = True
                        break
            
            if has_video:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            # Pass to super for internal drag-drop (reordering)
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
             event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            # External file drop
            files = []
            for url in mime.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    ext = os.path.splitext(path)[1].lower()
                    if ext in self.ACCEPTED_EXTENSIONS:
                        files.append(path)
            
            if files:
                self.files_dropped.emit(files)
                event.acceptProposedAction()
        else:
            # Internal move
            super().dropEvent(event)
