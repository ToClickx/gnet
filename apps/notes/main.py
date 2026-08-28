import os
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QInputDialog,
)
from PyQt6.QtCore import Qt
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Notes"
    app_id = "notes"
    app_version = "1.0.0"
    app_description = "Write notes stored in your app sandbox."

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.sandbox_file = os.path.join(self.bridge.sandbox_path, "notes.txt")
        self.current = os.path.basename(self.sandbox_file)

        self.setMinimumSize(520, 420)
        self.setWindowTitle("Notes")

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("My Note")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self.status = QLabel("")
        self.status.setStyleSheet("color: #888888;")
        header.addWidget(self.status)
        layout.addLayout(header)

        self.editor = QTextEdit()
        layout.addWidget(self.editor)

        buttons = QHBoxLayout()

        new_btn = QPushButton("New")
        new_btn.setFixedHeight(36)
        new_btn.clicked.connect(self.new_note)
        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self.save_note)
        open_btn = QPushButton("Open")
        open_btn.setFixedHeight(36)
        open_btn.clicked.connect(self.open_note)

        buttons.addWidget(new_btn)
        buttons.addWidget(open_btn)
        buttons.addWidget(save_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

    def main(self):
        self.load_current()

    def load_current(self):
        try:
            if os.path.isfile(self.sandbox_file):
                content = self.bridge.read_file(self.sandbox_file)
                self.editor.setPlainText(content)
                self.status.setText(f"Loaded {self.current}")
            else:
                self.editor.setPlainText("")
                self.status.setText(f"New note: {self.current}")
        except Exception as e:
            self.status.setText(f"Error: {e}")

    def save_note(self):
        try:
            self.bridge.write_file(self.sandbox_file, self.editor.toPlainText())
            self.status.setText(f"Saved {self.current}")
        except Exception as e:
            self.status.setText(f"Error: {e}")

    def new_note(self):
        self.editor.setPlainText("")
        self.current = "notes.txt"
        self.status.setText(f"New note: {self.current}")

    def open_note(self):
        name, ok = QInputDialog.getText(self, "Open note", "Filename (in sandbox):",
                                        text=self.current)
        if not ok or not name.strip():
            return
        self.current = name.strip()
        self.sandbox_file = os.path.join(self.bridge.sandbox_path, self.current)
        self.load_current()