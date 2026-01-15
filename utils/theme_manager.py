import sys
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

class ThemeManager:
    @staticmethod
    def apply_theme(app: QApplication, theme_name: str):
        # Resolve 'auto' to specific theme
        if theme_name == 'auto':
            if ThemeManager.is_system_dark():
                theme_name = 'dark'
            else:
                theme_name = 'light'

        # Apply the resolved theme
        if theme_name == 'dark':
            ThemeManager.set_dark_theme(app)
        else:
            ThemeManager.set_light_theme(app)

    @staticmethod
    def is_system_dark() -> bool:
        """Detects if Windows is in Dark Mode via Registry."""
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0 # 0 means Dark, 1 means Light
        except Exception:
            # Fallback for non-Windows or if key missing: default to Light or check simplistic heuristic
            pass
        return False

    @staticmethod
    def set_dark_theme(app: QApplication):
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        
        app.setPalette(palette)
        # Consistent minimal tooltip styling
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    @staticmethod
    def set_light_theme(app: QApplication):
        app.setStyle("Fusion")
        
        # Hardcoded Light Palette to ensure it looks Light even if system is Dark
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 231, 227))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(190, 190, 190))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(190, 190, 190))
        
        app.setPalette(palette)
        
        app.setStyleSheet("")
