import sys
import os

# Set up DLL search paths for Python 3.8+
# We need both PATH (for subprocesses/mpv internals) and add_dll_directory (for ctypes loading)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["PATH"] = script_dir + os.pathsep + os.environ.get("PATH", "")
if hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(script_dir)
    except Exception:
        pass

# Tell python-mpv to use libmpv-2.dll instead of mpv-2.dll
# mpv-2.dll has additional dependencies that may not be available
os.environ["MPV_DLL"] = os.path.join(script_dir, "libmpv-2.dll")

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()