import json
import os
from PyQt6.QtCore import QObject, pyqtSignal
from utils.settings import SettingsManager

class LanguageManager(QObject):
    language_changed = pyqtSignal()
    _instance = None

    def __init__(self):
        super().__init__()
        self._resource_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'lang')
        
        # Load from settings
        saved_lang = SettingsManager.instance().get("language", "ru")
        self._current_language = saved_lang
        self._translations = {}
        
        self.load_language(self._current_language)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_language(self, lang_code):
        file_path = os.path.join(self._resource_path, f'{lang_code}.json')
        if not os.path.exists(file_path):
            print(f"Language file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self._translations = json.load(f)
            self._current_language = lang_code
            self.language_changed.emit()
            
            # Save setting
            SettingsManager.instance().set("language", lang_code)
            
        except Exception as e:
            print(f"Error loading language {lang_code}: {e}")

    def tr(self, key):
        return self._translations.get(key, key)

    def set_language(self, lang_code):
        if self._current_language != lang_code:
            self.load_language(lang_code)

    def current_language(self):
        return self._current_language
