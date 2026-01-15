import os
import mpv
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTreeWidget, QTreeWidgetItem, QSplitter, 
                             QScrollBar, QFileDialog, QLabel, QTreeWidgetItemIterator,
                             QMenu, QInputDialog, QApplication, QProgressDialog, QMessageBox)
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QTimer

from ui.widgets.timeline import TimelineWidget
from ui.widgets.item_card import ItemCardWidget
from ui.widgets.video_tree import VideoTreeWidget
from ui.widgets.control_panel import ControlPanel
from ui.widgets.export_panel import ExportPanel
from ui.widgets.main_menu import MainMenu
from utils.language_manager import LanguageManager
from core.ffmpeg_core import FFmpegWorker
from core.export_processor import ExportThread
from core.ffmpeg_core import FFmpegWorker
from core.export_processor import ExportThread
from core.models import MediaItem, GroupItem
from utils.settings import SettingsManager
from utils.theme_manager import ThemeManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(LanguageManager.instance().tr("app_title"))
        self.resize(1500, 900)
        
        # Хранилище данных (путь : объект)
        self.video_data = {}

        self.init_ui()
        
        # Инициализация MPV
        self.player = mpv.MPV(wid=str(int(self.video_container.winId())), vo='gpu')
        self.init_observers()

        self.update_texts()
        LanguageManager.instance().language_changed.connect(self.update_texts)
        
        # Apply saved theme
        self.update_theme(SettingsManager.instance().get("theme", "auto"))

    def init_ui(self):
        # Setup Menu Bar
        self.menu = MainMenu(self)
        self.setMenuBar(self.menu)
        
        # Connect Menu Signals
        self.menu.add_video_triggered.connect(self.add_files_dialog)
        self.menu.delete_triggered.connect(self.confirm_delete_selection)
        self.menu.create_group_triggered.connect(self.create_group_from_selection)
        self.menu.delete_all_triggered.connect(self.confirm_clear_queue)
        self.menu.theme_changed.connect(self.update_theme)
        self.menu.about_triggered.connect(self.show_about)

        # Основной разделитель
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)

        # --- ЛЕВАЯ ПАНЕЛЬ: ОЧЕРЕДЬ И ГРУППЫ ---
        left_pane = QWidget()
        l_layout = QVBoxLayout(left_pane)
        
        self.lbl_queue = QLabel(f"<b>{LanguageManager.instance().tr('lbl_queue')}</b>")
        l_layout.addWidget(self.lbl_queue)
        self.group_counter = 1
        
        self.tree = VideoTreeWidget()
        self.tree.files_dropped.connect(self.add_video_files)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree.itemClicked.connect(self.on_item_clicked)
        l_layout.addWidget(self.tree)

        # Панель управления (Кнопки)
        self.control_panel = ControlPanel()
        self.control_panel.add_clicked.connect(self.add_files_dialog)
        self.control_panel.create_group_clicked.connect(self.create_group_from_selection)
        self.control_panel.clear_clicked.connect(self.confirm_clear_queue)
        l_layout.addWidget(self.control_panel)
        
        # Панель экспорта (Путь и кнопка)
        self.export_panel = ExportPanel()
        self.export_panel.select_dir_clicked.connect(self.select_output_dir)
        self.export_panel.export_clicked.connect(self.start_export)
        l_layout.addWidget(self.export_panel)

        # --- ПРАВАЯ ПАНЕЛЬ: РЕДАКТОР ---
        right_pane = QWidget()
        r_layout = QVBoxLayout(right_pane)

        # Контейнер видео
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background: black;")
        r_layout.addWidget(self.video_container, 7)

        # Скроллбар
        self.scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        r_layout.addWidget(self.scrollbar)

        # Таймлайн
        self.timeline = TimelineWidget()
        r_layout.addWidget(self.timeline, 1)

        # Connect selection change for clearing
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)

        # Нижние кнопки управления
        ctrls = QHBoxLayout()
        # Text, Function, Tooltip Key
        btns_data = [
            ("【", self.set_start, "tip_set_start"), 
            ("⏮", lambda: self.seek_keyframe(-1), "tip_prev_keyframe"), 
            ("◀", lambda: self.safe_frame_step(-1), "tip_prev_frame"), 
            ("⏯", lambda: self.player.cycle("pause"), "tip_play_pause"), 
            ("▶", lambda: self.safe_frame_step(1), "tip_next_frame"), 
            ("⏭", lambda: self.seek_keyframe(1), "tip_next_keyframe"), 
            ("】", self.set_end, "tip_set_end")
        ]
        
        self.player_btns = [] # Keep refs to update tooltips
        
        for text, func, tip_key in btns_data:
            b = QPushButton(text)
            b.setFixedWidth(50)
            b.clicked.connect(func)
            b.setProperty("tip_key", tip_key) # Store key for update_texts
            
            # Auto-repeat for navigation
            if text in ["◀", "▶", "⏮", "⏭"]:
                b.setAutoRepeat(True)
                b.setAutoRepeatDelay(300)
                b.setAutoRepeatInterval(50)
                
            ctrls.addWidget(b)
            self.player_btns.append(b)
            
        r_layout.addLayout(ctrls)

        # Настройка сплиттера
        self.splitter.addWidget(left_pane)
        self.splitter.addWidget(right_pane)
        self.splitter.setSizes([350, 1150])

        self.setup_connections()

    def setup_connections(self):
        # Связь таймлайна и плеера
        self.timeline.time_changed.connect(self.safe_seek)
        self.timeline.request_play_pause.connect(lambda: self.player.cycle("pause"))
        self.timeline.request_frame_step.connect(self.safe_frame_step)
        self.timeline.request_seek_keyframe.connect(self.seek_keyframe)
        self.timeline.request_set_marker.connect(lambda m: self.set_start() if m == 'start' else self.set_end())
        
        # Скролл
        self.timeline.ui_updated.connect(self.update_scroll)
        self.scrollbar.valueChanged.connect(self.manual_scroll)
        
        # Drag and Drop fix
        self.tree.model().rowsMoved.connect(self.on_rows_moved)
        self.tree.model().rowsInserted.connect(self.on_rows_inserted)

        # Delete Shortcut
        self.shortcut_del = QShortcut(QKeySequence("Delete"), self.tree)
        self.shortcut_del.activated.connect(self.confirm_delete_selection)

    def on_rows_moved(self, parent, start, end, destination, row):
        # QTimer для отложенного обновления, так как во время сигнала структура может быть не до конца обновлена
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._restore_widgets_after_move)

    def on_rows_inserted(self, parent, start, end):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._restore_widgets_after_move)

    def _restore_widgets_after_move(self):
        # Проходим по всем элементам и восстанавливаем виджеты, если их нет
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if not self.tree.itemWidget(item, 0):
                 data = item.data(0, Qt.ItemDataRole.UserRole)
                 if data:
                     card = self.create_item_widget(item, data)
                     self.tree.setItemWidget(item, 0, card)
            iterator += 1

    def init_observers(self):
        @self.player.property_observer('time-pos')
        def _on_time(name, val):
            if val is not None:
                self.timeline.current_time = val
                self.timeline.update()

        @self.player.property_observer('duration')
        def _on_dur(name, val):
            if val is not None:
                self.timeline.set_duration(val)

    # --- ЛОГИКА ОЧЕРЕДИ ---

    def create_item_widget(self, item, data):
        """Создает и настраивает виджет карточки для элемента дерева"""
        title = "Unknown"
        info = ""
        
        if isinstance(data, MediaItem):
            title = data.filename
            info = f"{data.fps} fps | {data.filename.split('.')[-1].upper()}"
        elif isinstance(data, GroupItem):
            title = f"📁 {data.name}"
            info = LanguageManager.instance().tr("lbl_bulk_marking")
            
        card = ItemCardWidget(title, info)
        card.tree_item = item  # Привязываем элемент к виджету для обработки событий
        
        # Настройка контекстного меню
        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(self.on_card_context_menu)
        
        # Восстанавливаем статус
        if data.is_ready:
            fps = getattr(data, 'fps', 25)
            dur = getattr(data, 'duration', 0)
            card.set_status(True, data.start_time, data.end_time, fps, dur)
            
        return card

    def on_card_context_menu(self, pos):
        """Обработчик ПКМ по карточке"""
        card = self.sender()
        if not card or not hasattr(card, 'tree_item'): return
        
        item = card.tree_item
        
        # Если элемент не выбран, выбираем его (очищая остальные, как в стандарте)
        if item not in self.tree.selectedItems():
             if not (QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier):
                 self.tree.clearSelection()
             item.setSelected(True)
        
        # Конвертируем позицию в координаты viewport дерева для вызова общего меню
        global_pos = card.mapToGlobal(pos)
        viewport_pos = self.tree.viewport().mapFromGlobal(global_pos)
        self.open_context_menu(viewport_pos)

    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Добавить видео в очередь", filter="Video Files (*.mp4 *.mkv *.avi *.mov *.flv *.webm *.wmv *.mpeg *.mpg)")
        if files:
            self.add_video_files(files)

    def add_video_files(self, files):
        if not files: return
        
        # Создаем прогресс-бар
        progress = QProgressDialog("Обработка видео...", "Отмена", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0) # Показывать сразу
        progress.setValue(0)
        
        for i, f in enumerate(files):
            if progress.wasCanceled():
                break
                
            progress.setLabelText(f"Обработка: {os.path.basename(f)}")
            
            if f not in self.video_data:
                fps, duration, kfs = FFmpegWorker.get_video_info(f)
                # В будущем можно добавить получение разрешения через ffprobe
                media = MediaItem(f, fps=fps, duration=duration, resolution="HD")
                
                item = QTreeWidgetItem(self.tree)
                # Запрещаем бросать в этот элемент (вложение в видео запрещено)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
                item.setData(0, Qt.ItemDataRole.UserRole, media)
                
                card = self.create_item_widget(item, media)
                self.tree.setItemWidget(item, 0, card)
                
                self.video_data[f] = media
            
            progress.setValue(i + 1)
            QApplication.processEvents() # Обновляем UI

        self.check_export_readiness()

    def confirm_delete_selection(self):
        selected = self.tree.selectedItems()
        if not selected: return
        
        lm = LanguageManager.instance()
        count = len(selected)
        answ = QMessageBox.question(self, lm.tr("action_delete"), lm.tr("msg_confirm_delete"),
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if answ == QMessageBox.StandardButton.Yes:
            self.delete_items(selected)

    def confirm_clear_queue(self):
        if self.tree.topLevelItemCount() == 0: return

        lm = LanguageManager.instance()
        answ = QMessageBox.question(self, lm.tr("btn_clear_list"), lm.tr("msg_confirm_clear"),
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if answ == QMessageBox.StandardButton.Yes:
            self.tree.clear()
            self.video_data.clear()
            self.group_counter = 1
            self.check_export_readiness()

    def create_group_from_selection(self):
        selected = self.tree.selectedItems()
        if not selected: return
        
        lm = LanguageManager.instance()
        group_name = f"{lm.tr('action_create_group').split(' ')[-1]} {self.group_counter:02}" # Simplify name logic or use localized default
        if "Group" in group_name or "Группа" in group_name: pass
        else: group_name = f"Group {self.group_counter:02}"

        self.group_counter += 1
        
        group_item = QTreeWidgetItem(self.tree)
        group_data = GroupItem(group_name)
        group_item.setData(0, Qt.ItemDataRole.UserRole, group_data)
        
        card = self.create_item_widget(group_item, group_data)
        self.tree.setItemWidget(group_item, 0, card)

        for item in selected:
            # Перемещаем в группу
            parent = item.parent() or self.tree.invisibleRootItem()
            index = parent.indexOfChild(item)
            child = parent.takeChild(index)
            group_item.addChild(child)
            
            # Восстанавливаем виджет для элемента в новой локации
            media = child.data(0, Qt.ItemDataRole.UserRole)
            if media:
                card = self.create_item_widget(child, media)
                self.tree.setItemWidget(child, 0, card)
        
        group_item.setExpanded(True)
        
        # --- СИНХРОНИЗАЦИЯ ПРИ СОЗДАНИИ ---
        # Ищем первое видео с метками (Master)
        master_child = None
        for i in range(group_item.childCount()):
            child = group_item.child(i)
            c_data = child.data(0, Qt.ItemDataRole.UserRole)
            if c_data and c_data.is_ready:
                master_child = c_data
                break
        
        # Если нашли, применяем его настройки ко всей группе
        if master_child:
            # Считаем параметры мастера
            m_start = master_child.start_time
            m_offset = max(0, master_child.duration - master_child.end_time)
            
            # Обновляем данные Группы
            group_data.start_time = m_start
            group_data.end_time = master_child.end_time
            group_data.is_ready = True
            
            # Обновляем виджет Группы
            gw = self.tree.itemWidget(group_item, 0)
            if gw:
                 fps = getattr(master_child, 'fps', 25)
                 dur = getattr(master_child, 'duration', 0)
                 gw.set_status(True, group_data.start_time, group_data.end_time, fps, dur)

            # Применяем ко всем детям
            for i in range(group_item.childCount()):
                child = group_item.child(i)
                c_data = child.data(0, Qt.ItemDataRole.UserRole)
                if c_data:
                    c_data.start_time = m_start
                    c_data.end_time = max(0, c_data.duration - m_offset)
                    c_data.is_ready = True
                    
                    cw = self.tree.itemWidget(child, 0)
                    if cw:
                        cw.set_status(True, c_data.start_time, c_data.end_time, c_data.fps, c_data.duration)

        self.check_export_readiness()

    def open_context_menu(self, position):
        menu = QMenu()
        selected = self.tree.selectedItems()
        
        if not selected: return

        # Проверяем, есть ли среди выбранных группа (для переименования)
        has_group = any(isinstance(item.data(0, Qt.ItemDataRole.UserRole), GroupItem) for item in selected)
        
        if has_group and len(selected) == 1:
            rename_action = menu.addAction("✏️ Переименовать")
            rename_action.triggered.connect(lambda: self.rename_group(selected[0]))
        
        delete_action = menu.addAction("❌ Удалить")
        delete_action.triggered.connect(lambda: self.delete_items(selected))
        
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def rename_group(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, GroupItem): return
        
        new_name, ok = QInputDialog.getText(self, "Переименовать группу", "Новое имя:", text=data.name)
        if ok and new_name:
            data.name = new_name
            # Обновляем карточку
            card = self.create_item_widget(item, data)
            self.tree.setItemWidget(item, 0, card)

    def delete_items(self, items):
        for item in items:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            parent = item.parent() or self.tree.invisibleRootItem()
            
            if isinstance(data, GroupItem):
                # Разгруппировка: перемещаем детей в корень
                children = []
                for i in range(item.childCount()):
                    children.append(item.child(i))
                
                for child in children:
                    item.removeChild(child)
                    parent.addChild(child) # Добавляем в конец корня (или родителя группы если вложенность)
                    
                    # Восстанавливаем виджет (так как при перемещении он теряется)
                    c_data = child.data(0, Qt.ItemDataRole.UserRole)
                    if c_data:
                        card = self.create_item_widget(child, c_data)
                        self.tree.setItemWidget(child, 0, card)
                
                # Удаляем саму группу
                parent.removeChild(item)
                
            elif isinstance(data, MediaItem):
                # Удаление видео
                if data.path in self.video_data:
                    del self.video_data[data.path]
                parent.removeChild(item)
        
        self.check_export_readiness()
    
    def on_item_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        target_media = None
        if isinstance(data, MediaItem):
            target_media = data
        elif isinstance(data, GroupItem) and item.childCount() > 0:
            # Загружаем Master-клип (первый в группе)
            first_child = item.child(0)
            target_media = first_child.data(0, Qt.ItemDataRole.UserRole)

        if target_media:
            self.player.play(target_media.path)
            self.player.pause = True
            
            # Обновляем таймлайн данными текущего видео
            fps, duration, kfs = FFmpegWorker.get_video_info(target_media.path)
            self.timeline.fps = fps
            self.timeline.keyframes = kfs
            
            # Восстанавливаем маркеры
            self.timeline.start_marker = target_media.start_time
            self.timeline.end_marker = target_media.end_time or self.timeline.duration
            
            self.timeline.update_all()
            self.timeline.setFocus()

    # --- УПРАВЛЕНИЕ МАРКЕРАМИ ---

    def set_start(self):
        t = self.player.time_pos or 0
        self.timeline.start_marker = t
        self._sync_markers_to_data('start', t)
        self.timeline.update()

    def set_end(self):
        t = self.player.time_pos or self.timeline.duration
        self.timeline.end_marker = t
        self._sync_markers_to_data('end', t)
        self.timeline.update()

    def _sync_markers_to_data(self, mode, val):
        item = self.tree.currentItem()
        if not item: return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Helper для обновления виджета
        def update_widget(tree_item, d):
            w = self.tree.itemWidget(tree_item, 0)
            if w:
                fps = getattr(d, 'fps', 25)
                dur = getattr(d, 'duration', 0)
                w.set_status(True, d.start_time, d.end_time, fps, dur)
        
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.check_export_readiness)

        if isinstance(data, GroupItem):
            # Применяем ко всем видео в группе
            # Для группы считаем offset если end
            offset_from_end = 0
            if mode == 'end':
                data.end_time = val
            else:
                 data.start_time = val
            data.is_ready = True
            
            # Получаем текущее видео в плеере, чтобы понять отступ
            current_duration = self.player.duration or 0
            offset = max(0, current_duration - val) if mode == 'end' else 0

            for i in range(item.childCount()):
                child = item.child(i)
                child_data = child.data(0, Qt.ItemDataRole.UserRole)
                
                if mode == 'start': 
                    child_data.start_time = val
                else: 
                    # RELATIVE LOGIC
                    child_data.end_time = max(0, child_data.duration - offset)
                
                child_data.is_ready = True
                update_widget(child, child_data)
            
            # Обновляем саму группу
            update_widget(item, data)
        
        elif isinstance(data, MediaItem):
            # Проверяем, находится ли элемент в группе
            parent = item.parent()
            if parent:
                p_data = parent.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(p_data, GroupItem):
                    # Логика группы: применяем ко всем
                    
                    # Считаем offset
                    offset = 0
                    if mode == 'end':
                        offset = max(0, data.duration - val)
                    
                    # Обновляем группу (визуально)
                    if mode == 'start': p_data.start_time = val
                    else: p_data.end_time = val # Тут спорно что писать в группу, но пусть будет абсолют текущего
                    p_data.is_ready = True
                    update_widget(parent, p_data)
                    
                    # Обновляем всех детей (включая текущий)
                    for i in range(parent.childCount()):
                        child = parent.child(i)
                        c_data = child.data(0, Qt.ItemDataRole.UserRole)
                        
                        if mode == 'start': 
                            c_data.start_time = val
                        else: 
                            # RELATIVE LOGIC
                            c_data.end_time = max(0, c_data.duration - offset)
                            
                        c_data.is_ready = True
                        update_widget(child, c_data)
                    return

            # Обычный режим (одиночное видео)
            if mode == 'start': data.start_time = val
            else: data.end_time = val
            data.is_ready = True
            update_widget(item, data)

    # --- БЕЗОПАСНЫЕ КОМАНДЫ ПЛЕЕРА ---

    def safe_seek(self, t):
        try: self.player.time_pos = t
        except: pass

    def safe_frame_step(self, d):
        try:
            if d > 0:
                if (self.player.time_pos or 0) < (self.player.duration or 0) - 0.01:
                    self.player.command("frame-step")
            else:
                if (self.player.time_pos or 0) > 0.01:
                    self.player.command("frame-back-step")
        except: pass

    def seek_keyframe(self, d):
        kfs = self.timeline.keyframes
        if not kfs: return
        curr = self.player.time_pos or 0
        try:
            target = next((k for k in (kfs if d > 0 else reversed(kfs)) 
                          if (k > curr + 0.1 if d > 0 else k < curr - 0.1)), curr)
            self.player.time_pos = target
        except: pass

    # --- СКРОЛЛИНГ ---

    def update_scroll(self, off, tot, vis):
        self.scrollbar.blockSignals(True)
        self.scrollbar.setRange(0, max(0, tot - vis))
        self.scrollbar.setPageStep(vis)
        self.scrollbar.setValue(off)
        self.scrollbar.blockSignals(False)

    def manual_scroll(self, val):
        if self.timeline.zoom > 0:
            self.timeline.offset_s = val / self.timeline.zoom
            self.timeline.update_all()

    # --- ЭКСПОРТ ---

    def select_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, LanguageManager.instance().tr("lbl_select_folder"))
        if d:
            self.export_panel.set_output_path(d)

    def check_export_readiness(self):
        # Проверяем, что есть хотя бы одно видео и ВСЕ они готовы
        has_items = False
        all_ready = True
        
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            data = item.data(0, Qt.ItemDataRole.UserRole)
            
            if isinstance(data, MediaItem):
                has_items = True
                if not data.is_ready:
                    all_ready = False
                    break
            elif isinstance(data, GroupItem):
                pass
                
            iterator += 1
            
        self.export_panel.set_export_enabled(has_items and all_ready)

    def start_export(self):
        output_dir = self.export_panel.get_output_path()
        if not output_dir:
            QMessageBox.warning(self, "Ошибка", "Выберите папку для сохранения видео!")
            return
            
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except:
                QMessageBox.warning(self, "Ошибка", f"Не удалось создать папку: {output_dir}")
                return

        # Собираем список файлов для экспорта
        export_items = []
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(data, MediaItem) and data.is_ready:
                export_items.append(data)
            iterator += 1
            
        if not export_items:
            QMessageBox.warning(self, "Внимание", "Нет готовых видео для экспорта.")
            return

        # Настраиваем прогресс-бар
        self.progress_dialog = QProgressDialog("Подготовка к экспорту...", "Отмена", 0, len(export_items), self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        
        # Запускаем поток
        self.export_thread = ExportThread(export_items, output_dir)
        self.export_thread.progress_update.connect(self.on_export_progress)
        self.export_thread.finished_all.connect(self.on_export_finished)
        self.export_thread.log_message.connect(lambda msg: print(f"Export Log: {msg}")) 
        
        # Отмена
        self.progress_dialog.canceled.connect(self.cancel_export)
        
        self.export_thread.start()

    def on_export_progress(self, current, total, filename):
        self.progress_dialog.setValue(current)
        self.progress_dialog.setLabelText(f"Экспорт ({current + 1}/{total}):\n{filename}")

    def on_export_finished(self):
        self.progress_dialog.setValue(self.progress_dialog.maximum())
        self.progress_dialog.close()
        QMessageBox.information(self, "Готово", "Экспорт успешно завершен!")
        self.export_thread = None

    def cancel_export(self):
        if self.export_thread:
            self.export_thread.is_running = False
            self.export_thread.wait()
            self.export_thread = None

    # --- NEW METHODS ---

    def on_selection_changed(self):
        if not self.tree.selectedItems():
            # Clear player and timeline
            self.player.loadfile("")
            self.timeline.set_duration(0)
            self.timeline.start_marker = 0
            self.timeline.end_marker = 0
            self.timeline.keyframes = []
            self.timeline.update_all()
            # Check export readiness instead of unconditionally disabling
            self.check_export_readiness()
            self.setWindowTitle(LanguageManager.instance().tr("app_title"))
            
    def update_texts(self):
        lm = LanguageManager.instance()
        self.setWindowTitle(lm.tr("app_title"))
        self.lbl_queue.setText(f"<b>{lm.tr('lbl_queue')}</b>")
        
        # Update player buttons tooltips
        if hasattr(self, 'player_btns'):
            for b in self.player_btns:
                key = b.property("tip_key")
                if key: b.setToolTip(lm.tr(key))
        
        # Update tree items
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(data, GroupItem):
                 w = self.tree.itemWidget(item, 0)
                 if w: w.set_info(lm.tr("lbl_bulk_marking"))
            iterator += 1

    def update_theme(self, theme):
        ThemeManager.apply_theme(QApplication.instance(), theme)
        
        # Determine internal theme string for timeline
        if theme == 'light':
            tl_theme = 'light'
            bg_color = "#f0f0f0"
        else:
            tl_theme = 'dark'
            bg_color = "black"
            
        self.timeline.set_theme(tl_theme)
        self.video_container.setStyleSheet(f"background: {bg_color};")
            
    def show_about(self):
         lm = LanguageManager.instance()
         hotkeys = lm.tr("msg_about_hotkeys")
         QMessageBox.about(self, lm.tr("action_about"),
                           f"Pro Video Trimmer 2025\nVersion 1.0\n\n{hotkeys}")
