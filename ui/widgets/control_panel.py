from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from utils.language_manager import LanguageManager

class ControlPanel(QWidget):
    add_clicked = pyqtSignal()
    create_group_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        LanguageManager.instance().language_changed.connect(self.update_texts)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_add = QPushButton()
        self.btn_add.clicked.connect(self.add_clicked)
        
        self.btn_group = QPushButton()
        self.btn_group.clicked.connect(self.create_group_clicked)
        
        self.btn_clear = QPushButton()
        self.btn_clear.setFixedWidth(40)
        self.btn_clear.clicked.connect(self.clear_clicked)
        
        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_group)
        layout.addWidget(self.btn_clear)
        
        self.update_texts()

    def update_texts(self):
        lm = LanguageManager.instance()
        self.btn_add.setText("➕ " + lm.tr("btn_add_files"))
        self.btn_add.setToolTip(lm.tr("btn_add_files"))
        self.btn_group.setText("📁 " + lm.tr("btn_create_group"))
        self.btn_group.setToolTip(lm.tr("btn_create_group"))
        self.btn_clear.setText("🗑️")
        self.btn_clear.setToolTip(lm.tr("btn_clear_list"))
