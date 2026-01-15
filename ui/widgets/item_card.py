from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from utils.helpers import format_time_hmsf
from utils.language_manager import LanguageManager

class ItemCardWidget(QWidget):
    def __init__(self, title, info_str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Store initial data for updates (title/info might be updated externally or need handling)
        self.title_text = title
        self.info_text = info_str
        
        # Store status for re-rendering on lang change
        self.status_data = (False, 0, 0, 25, 0) # is_ready, start, end, fps, duration

        # Внешний лейаут для отступов между карточками
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 2, 0, 2)  # Отступы сверху и снизу
        outer_layout.setSpacing(0)
        
        # Внутренняя рамка с контентом
        self.frame = QFrame()
        self.frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Стандартный стиль (Red / Muted)
        self.default_style = """
            QFrame {
                background-color: #8e0000; 
                border: 1px solid #b71c1c; 
                border-radius: 4px;
            }
            QLabel { color: #e0e0e0; border: none; background: transparent; }
        """
        self.ready_style = """
            QFrame {
                background-color: #1b5e20; 
                border: 1px solid #2e7d32; 
                border-radius: 4px;
            }
            QLabel { color: #fff; border: none; background: transparent; }
        """
        self.frame.setStyleSheet(self.default_style)
        
        inner_layout = QVBoxLayout(self.frame)
        inner_layout.setContentsMargins(8, 6, 8, 6)
        inner_layout.setSpacing(2)

        self.title_label = QLabel(f"<b>{title}</b>")
        self.info_label = QLabel(info_str)
        self.info_label.setStyleSheet("font-size: 11px; color: #ccc;")
        
        self.marker_label = QLabel()
        self.marker_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffcdd2;")

        inner_layout.addWidget(self.title_label)
        inner_layout.addWidget(self.info_label)
        inner_layout.addWidget(self.marker_label)
        
        outer_layout.addWidget(self.frame)
        
        LanguageManager.instance().language_changed.connect(self.update_texts)
        self.update_texts()

    def set_status(self, is_ready, start=0, end=0, fps=25, duration=0):
        self.status_data = (is_ready, start, end, fps, duration)
        self.update_texts()

    def update_texts(self):
        lm = LanguageManager.instance()
        is_ready, start, end, fps, duration = self.status_data
        
        if is_ready:
            self.frame.setStyleSheet(self.ready_style)
            self.marker_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #c8e6c9;")
            
            # Format START
            start_str = format_time_hmsf(start, fps)
            
            # Format END (Relative if duration > 0)
            if duration > 0:
                offset = max(0, duration - end)
                end_str = f"-{format_time_hmsf(offset, fps)}"
            else:
                end_str = format_time_hmsf(end, fps)
                
            self.marker_label.setText(f"IN: {start_str} | OUT: {end_str}")
        else:
            self.frame.setStyleSheet(self.default_style)
            self.marker_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffcdd2;")
            self.marker_label.setText(lm.tr("lbl_need_marking"))
            
    def set_info(self, text):
        self.info_text = text
        self.info_label.setText(text)
