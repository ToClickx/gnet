from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QListWidgetItem, QLabel,
)
from PyQt6.QtCore import Qt
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "To-Do"
    app_id = "todo"
    app_version = "1.0.0"
    app_description = "A personal to-do list stored per user."

    FIELD_KEY = "todo_items"

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.items = []

        self.setMinimumSize(420, 480)
        self.setWindowTitle("To-Do")

        layout = QVBoxLayout(self)

        title = QLabel("My To-Do List")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #888888;")
        layout.addWidget(self.status)

        entry = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Add a task...")
        self.input_box.returnPressed.connect(self.add_item)
        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self.add_item)
        entry.addWidget(self.input_box)
        entry.addWidget(add_btn)
        layout.addLayout(entry)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.remove_item)
        layout.addWidget(self.list_widget)

        actions = QHBoxLayout()
        remove_btn = QPushButton("Remove")
        remove_btn.setFixedWidth(100)
        remove_btn.clicked.connect(self.remove_selected)
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_all)
        actions.addWidget(remove_btn)
        actions.addWidget(clear_btn)
        actions.addStretch()
        layout.addLayout(actions)

    def main(self):
        self.load_items()

    def load_items(self):
        try:
            stored = self.bridge.get_user_field(self.FIELD_KEY)
            if isinstance(stored, list):
                self.items = list(stored)
        except Exception:
            self.items = []
        self.render()

    def save_items(self):
        try:
            self.bridge.set_user_field(self.FIELD_KEY, self.items)
            self.status.setText("Saved to your account.")
        except Exception as e:
            self.status.setText(f"Save error: {e}")

    def add_item(self):
        text = self.input_box.text().strip()
        if not text:
            return
        self.items.append(text)
        self.input_box.clear()
        self.render()
        self.save_items()

    def remove_item(self, item):
        self.items.remove(item.text())
        self.render()
        self.save_items()

    def remove_selected(self):
        selected = self.list_widget.selectedItems()
        for item in selected:
            if item.text() in self.items:
                self.items.remove(item.text())
        self.render()
        self.save_items()

    def clear_all(self):
        self.items = []
        self.render()
        self.save_items()

    def render(self):
        self.list_widget.clear()
        for text in self.items:
            item = QListWidgetItem(text)
            self.list_widget.addItem(item)