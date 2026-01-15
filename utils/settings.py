import json
import os

class SettingsManager:
    _instance = None
    
    def __init__(self):
        self._settings = {
            "language": "ru",
            "theme": "auto"
        }
        # Config folder next to main.py (parent of utils)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self._config_dir = os.path.join(base_dir, 'config')
        self._config_file = os.path.join(self._config_dir, 'settings.json')
        
        self.load()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self):
        if not os.path.exists(self._config_file):
            return
            
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._settings.update(data)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save(self):
        if not os.path.exists(self._config_dir):
            try:
                os.makedirs(self._config_dir)
            except Exception as e:
                print(f"Error creating config dir: {e}")
                return

        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save()
