from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QWheelEvent, QMouseEvent
from utils.helpers import format_time_hmsf

class TimelineWidget(QWidget):
    time_changed = pyqtSignal(float)
    ui_updated = pyqtSignal(int, int, int) 
    request_seek_keyframe = pyqtSignal(int)
    request_set_marker = pyqtSignal(str) 
    request_frame_step = pyqtSignal(int) 
    request_play_pause = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(120)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.duration = self.current_time = 0.0
        self.start_marker = self.end_marker = 0.0
        self.keyframes = []
        self.fps = 25.0
        self.zoom = 1.0   
        self.offset_s = 0.0 
        
        self.is_dragging_cursor = self.is_panning = False
        self.setMouseTracking(True)
        
        # Theme colors
        self.theme = 'dark'
        self.colors = {
            'dark': {
                'bg': QColor(30, 30, 30),
                'ruler_bg': QColor(40, 40, 40),
                'border': QColor(0, 150, 255, 100),
                'tick': QColor(150, 150, 150),
                'text': Qt.GlobalColor.white,
                'keyframe': QColor(100, 100, 100, 150),
                'cut_zone': QColor(0, 255, 0, 20),
                'cursor_color': QColor(0, 180, 255),
                'cursor_text': Qt.GlobalColor.white
            },
            'light': {
                'bg': QColor(240, 240, 240),
                'ruler_bg': QColor(220, 220, 220),
                'border': QColor(0, 120, 215, 150),
                'tick': QColor(80, 80, 80),
                'text': Qt.GlobalColor.black,
                'keyframe': QColor(100, 100, 100, 100),
                'cut_zone': QColor(0, 255, 0, 40),
                'cursor_color': QColor(0, 120, 215),
                'cursor_text': Qt.GlobalColor.black
            }
        }
        
        # Таймер для плавного авто-скроллинга у краев
        self.edge_scroll_timer = QTimer()
        self.edge_scroll_timer.setInterval(30)
        self.edge_scroll_timer.timeout.connect(self.check_edge_scroll)
        self.scroll_direction = 0 # -1 влево, 1 вправо

    def set_theme(self, theme_name):
        self.theme = theme_name if theme_name in ['dark', 'light'] else 'dark'
        self.update()

    def set_duration(self, duration):
        self.duration = duration
        if self.width() > 0:
            self.zoom = self.width() / max(0.001, self.duration)
        self.offset_s = 0
        self.update_all()

    def update_all(self):
        min_zoom = self.width() / max(0.001, self.duration)
        self.zoom = max(self.zoom, min_zoom)
        max_offset = max(0, self.duration - (self.width() / self.zoom))
        self.offset_s = max(0, min(self.offset_s, max_offset))
        self.ui_updated.emit(int(self.offset_s * self.zoom), int(self.duration * self.zoom), self.width())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()
        ruler_h = 30
        
        c = self.colors.get(self.theme, self.colors['dark'])
        
        painter.fillRect(0, 0, w, h, c['bg'])
        painter.fillRect(0, 0, w, ruler_h, c['ruler_bg'])

        if self.hasFocus():
            painter.setPen(QPen(c['border'], 1))
            painter.drawRect(0, 0, w-1, h-1)

        if self.duration <= 0: return

        # Линейка
        intervals = [1/self.fps, 5/self.fps, 1, 2, 5, 10, 30, 60, 300]
        chosen = next((i for i in intervals if i * self.zoom > 80), intervals[-1])
        t = (self.offset_s // chosen) * chosen
        
        painter.setPen(QPen(c['tick'], 1))
        
        while t < self.offset_s + (w / self.zoom) + chosen:
            x = int((t - self.offset_s) * self.zoom)
            if 0 <= x <= w:
                painter.drawLine(x, ruler_h - 10, x, ruler_h)
                
                # Текст всегда рисовать после установки ручки
                painter.setPen(c['text'])
                painter.drawText(x + 3, ruler_h - 5, format_time_hmsf(t, self.fps))
                painter.setPen(QPen(c['tick'], 1)) # Возврат к цвету рисок
            t += chosen

        # Ключевые кадры
        painter.setPen(QPen(c['keyframe'], 1))
        for kf in self.keyframes:
            kx = int((kf - self.offset_s) * self.zoom)
            if 0 <= kx <= w: painter.drawLine(kx, ruler_h + 5, kx, h)

        # Зона обрезки
        x_s, x_e = int((self.start_marker - self.offset_s) * self.zoom), int((self.end_marker - self.offset_s) * self.zoom)
        painter.fillRect(max(0, x_s), ruler_h, min(w, x_e) - max(0, x_s), h, c['cut_zone'])
        
        # Линии маркеров
        # Start (Зеленая линия)
        if 0 <= x_s <= w:
             painter.setPen(QPen(QColor(0, 200, 0), 2))
             painter.drawLine(x_s, ruler_h, x_s, h)
        
        # End (Красная линия)
        if 0 <= x_e <= w:
             painter.setPen(QPen(QColor(255, 50, 50), 2))
             painter.drawLine(x_e, ruler_h, x_e, h)

        # Курсор
        curr_x = int((self.current_time - self.offset_s) * self.zoom)
        if 0 <= curr_x <= w:
            painter.setPen(QPen(c['cursor_color'], 1)); painter.drawLine(curr_x, 0, curr_x, h)
            painter.setBrush(c['cursor_color']); painter.drawRect(curr_x - 5, 0, 10, 15)
            
            # Умное отображение времени (влево или вправо)
            time_str = f"{format_time_hmsf(self.current_time, self.fps)} | F: {int(self.current_time * self.fps)}"
            text_w = painter.fontMetrics().horizontalAdvance(time_str)
            text_x = curr_x + 10 if curr_x + text_w + 20 < w else curr_x - text_w - 10
            
            painter.setPen(c['cursor_text'])
            painter.drawText(text_x, 15, time_str)

    def mouseMoveEvent(self, event: QMouseEvent):
        x = event.position().x()
        if self.is_dragging_cursor:
            # Логика авто-скролла
            margin = 40
            if x < margin:
                self.scroll_direction = -1
                if not self.edge_scroll_timer.isActive(): self.edge_scroll_timer.start()
            elif x > self.width() - margin:
                self.scroll_direction = 1
                if not self.edge_scroll_timer.isActive(): self.edge_scroll_timer.start()
            else:
                self.scroll_direction = 0
                self.edge_scroll_timer.stop()

            t = max(0, min((x / self.zoom) + self.offset_s, self.duration))
            self.time_changed.emit(t)

        elif self.is_panning:
            self.offset_s -= (x - self.last_mouse_x) / self.zoom
            self.last_mouse_x = x
            self.update_all()

    def check_edge_scroll(self):
        if not self.is_dragging_cursor:
            self.edge_scroll_timer.stop()
            return
        
        scroll_speed = 5 / self.zoom # 5 пикселей в секундах
        self.offset_s += self.scroll_direction * scroll_speed
        self.update_all()
        # Обновляем время под курсором в зависимости от нового смещения
        cursor_pos_x = self.mapFromGlobal(self.cursor().pos()).x()
        t = max(0, min((cursor_pos_x / self.zoom) + self.offset_s, self.duration))
        self.time_changed.emit(t)

    def mouseReleaseEvent(self, event):
        self.is_dragging_cursor = self.is_panning = False
        self.edge_scroll_timer.stop()

    def mousePressEvent(self, event: QMouseEvent):
        self.setFocus()
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging_cursor = True
            self.time_changed.emit((event.position().x() / self.zoom) + self.offset_s)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_mouse_x = event.position().x()

    def wheelEvent(self, event: QWheelEvent):
        anchor_t = self.current_time
        anchor_x = int((anchor_t - self.offset_s) * self.zoom)
        self.zoom *= 1.2 if event.angleDelta().y() > 0 else 1/1.2
        self.offset_s = anchor_t - (anchor_x / self.zoom)
        self.update_all()

    def keyPressEvent(self, event):
        key, mod, txt = event.key(), event.modifiers(), event.text().lower()
        if key == Qt.Key.Key_Space: self.request_play_pause.emit()
        elif key == Qt.Key.Key_Right:
            if mod & Qt.KeyboardModifier.ControlModifier: self.request_frame_step.emit(1)
            else: self.request_seek_keyframe.emit(1)
        elif key == Qt.Key.Key_Left:
            if mod & Qt.KeyboardModifier.ControlModifier: self.request_frame_step.emit(-1)
            else: self.request_seek_keyframe.emit(-1)
        elif key in [Qt.Key.Key_BracketLeft, Qt.Key.Key_BracketRight] or txt in ["[", "х", "]", "ъ"]:
            self.request_set_marker.emit('start' if txt in ["[", "х"] else 'end')