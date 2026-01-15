from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import pyqtSignal
from utils.language_manager import LanguageManager
from utils.settings import SettingsManager

class MainMenu(QMenuBar):
    # File
    add_video_triggered = pyqtSignal()
    
    # Edit
    delete_triggered = pyqtSignal()
    create_group_triggered = pyqtSignal()
    delete_all_triggered = pyqtSignal()
    
    # View
    theme_changed = pyqtSignal(str) # 'dark', 'light', 'auto'
    language_changed = pyqtSignal(str) # 'en', 'ru'
    
    # Info
    about_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        LanguageManager.instance().language_changed.connect(self.update_texts)

    def init_ui(self):
        # File
        self.menu_file = self.addMenu("File")
        self.act_add = QAction("Add Video", self)
        self.act_add.triggered.connect(self.add_video_triggered)
        self.menu_file.addAction(self.act_add)

        # Edit
        self.menu_edit = self.addMenu("Edit")
        self.act_delete = QAction("Delete", self)
        self.act_delete.triggered.connect(self.delete_triggered)
        self.act_create_group = QAction("Create Group", self)
        self.act_create_group.triggered.connect(self.create_group_triggered)
        self.act_delete_all = QAction("Delete All", self)
        self.act_delete_all.triggered.connect(self.delete_all_triggered)
        
        self.menu_edit.addAction(self.act_delete)
        self.menu_edit.addAction(self.act_create_group)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_delete_all)

        # View
        self.menu_view = self.addMenu("View")
        
        # Theme Submenu
        self.menu_theme = self.menu_view.addMenu("Theme")
        theme_group = QActionGroup(self)
        self.act_theme_dark = QAction("Dark", self, checkable=True)
        self.act_theme_dark.setData('dark')
        self.act_theme_light = QAction("Light", self, checkable=True)
        self.act_theme_light.setData('light')
        self.act_theme_auto = QAction("Auto", self, checkable=True)
        self.act_theme_auto.setData('auto')
        
        # Check saved setting
        saved_theme = SettingsManager.instance().get("theme", "auto")
        if saved_theme == 'dark': self.act_theme_dark.setChecked(True)
        elif saved_theme == 'light': self.act_theme_light.setChecked(True)
        else: self.act_theme_auto.setChecked(True)
        
        for act in [self.act_theme_dark, self.act_theme_light, self.act_theme_auto]:
            theme_group.addAction(act)
            self.menu_theme.addAction(act)
        theme_group.triggered.connect(lambda a: self.on_theme_triggered(a.data()))
        
        # Language Submenu
        self.menu_lang = self.menu_view.addMenu("Language")
        lang_group = QActionGroup(self)
        self.act_lang_en = QAction("English", self, checkable=True)
        self.act_lang_en.setData('en')
        self.act_lang_ru = QAction("Russian", self, checkable=True)
        self.act_lang_ru.setData('ru')
        
        # Set checked based on current
        current_lang = LanguageManager.instance().current_language()
        if current_lang == 'ru': self.act_lang_ru.setChecked(True)
        else: self.act_lang_en.setChecked(True)

        for act in [self.act_lang_en, self.act_lang_ru]:
            lang_group.addAction(act)
            self.menu_lang.addAction(act)
        lang_group.triggered.connect(lambda a: self.on_language_triggered(a.data()))

        # Info
        self.menu_info = self.addMenu("Info")
        self.act_about = QAction("About", self)
        self.act_about.triggered.connect(self.about_triggered)
        
        self.menu_info.addAction(self.act_about)

        self.update_texts()
        
    def on_theme_triggered(self, theme_code):
        SettingsManager.instance().set("theme", theme_code)
        self.theme_changed.emit(theme_code)

    def on_language_triggered(self, lang_code):
        LanguageManager.instance().set_language(lang_code)
        # Settings are saved inside LanguageManager, so we don't need to save here, or we can double check.
        # But wait, LanguageManager.set_language calls load_language which saves settings.
        # We also need to emit signal if needed by others, but mostly LM handles it.
        self.language_changed.emit(lang_code)

    def update_texts(self):
        lm = LanguageManager.instance()
        
        self.menu_file.setTitle(lm.tr("menu_file"))
        self.act_add.setText(lm.tr("action_add_video"))
        
        self.menu_edit.setTitle(lm.tr("menu_edit"))
        self.act_delete.setText(lm.tr("action_delete"))
        self.act_create_group.setText(lm.tr("action_create_group"))
        self.act_delete_all.setText(lm.tr("action_delete_all"))
        
        self.menu_view.setTitle(lm.tr("menu_view"))
        self.menu_theme.setTitle(lm.tr("menu_theme_title"))
        
        self.act_theme_dark.setText(lm.tr("action_theme_dark"))
        self.act_theme_light.setText(lm.tr("action_theme_light"))
        self.act_theme_auto.setText(lm.tr("action_theme_auto"))
        
        self.menu_lang.setTitle(lm.tr("menu_lang_title"))
        self.act_lang_en.setText(lm.tr("action_lang_en"))
        self.act_lang_ru.setText(lm.tr("action_lang_ru"))
        
        self.menu_info.setTitle(lm.tr("menu_info"))
        self.act_about.setText(lm.tr("action_about"))
