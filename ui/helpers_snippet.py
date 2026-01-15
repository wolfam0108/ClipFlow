# Helper Methods needed in main_window.py

```python
    def create_item_widget(self, item, data):
        """Создает и настраивает виджет карточки для элемента дерева"""
        title = "Unknown"
        info = ""
        
        if isinstance(data, MediaItem):
            title = data.filename
            info = f"{data.fps} fps | {data.filename.split('.')[-1].upper()}"
        elif isinstance(data, GroupItem):
            title = f"📁 {data.name}"
            info = "Массовая разметка"
            
        card = ItemCardWidget(title, info)
        card.tree_item = item  # Привязываем элемент к виджету
        
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
        
        # Если элемент не выбран, выбираем его
        if item not in self.tree.selectedItems():
             if not (QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier):
                 self.tree.clearSelection()
             item.setSelected(True)
        
        # Конвертируем позицию
        global_pos = card.mapToGlobal(pos)
        viewport_pos = self.tree.viewport().mapFromGlobal(global_pos)
        self.open_context_menu(viewport_pos)
```
