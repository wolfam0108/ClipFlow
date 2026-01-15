from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit
from PyQt6.QtCore import pyqtSignal
from utils.language_manager import LanguageManager

class ExportPanel(QWidget):
    select_dir_clicked = pyqtSignal()
    export_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        LanguageManager.instance().language_changed.connect(self.update_texts)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Output Path Row
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedWidth(30)
        self.btn_browse.clicked.connect(self.select_dir_clicked)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.btn_browse)
        
        layout.addLayout(path_layout)
        
        # Export Button
        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self.export_clicked)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #1b5e20; 
                color: white; 
                font-weight: bold; 
                padding: 12px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)
        
        layout.addWidget(self.btn_export)
        
        self.update_texts()

    def update_texts(self):
        lm = LanguageManager.instance()
        self.path_edit.setPlaceholderText(lm.tr("lbl_output_folder"))
        self.btn_export.setText("🚀 " + lm.tr("btn_export"))

    def set_output_path(self, path):
        self.path_edit.setText(path)

    def get_output_path(self):
        return self.path_edit.text()

    def set_export_enabled(self, enabled):
        self.btn_export.setEnabled(enabled)
