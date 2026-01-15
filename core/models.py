import os

class MediaItem:
    def __init__(self, path, fps=25.0, duration=0.0, resolution="Unknown"):
        self.path = path
        self.filename = os.path.basename(path)
        self.fps = fps
        self.duration = duration
        self.resolution = resolution
        self.start_time = 0.0
        self.end_time = duration
        self.is_ready = False  # Статус (Зеленый/Красный)

class GroupItem:
    def __init__(self, name):
        self.name = name
        self.items = [] # Список MediaItem
        self.start_time = 0.0
        self.end_time = 0.0
        self.is_ready = False