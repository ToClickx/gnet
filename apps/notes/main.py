import os
import datetime

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QInputDialog,
    QListWidget, QListWidgetItem, QMessageBox, QWidget,
)
from PyQt6.QtCore import Qt
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Notes"
    app_id = "notes"
    app_version = "1.1.0"
    app_description = "Write and manage notes stored in your app sandbox."

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.current_file = None

        self.setMinimumSize(640, 460)
        self.setWindowTitle("Notes")

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("My Notes")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        self.file_label = QLabel("No note open")
        self.file_label.setStyleSheet("color: #888888;")
        header.addWidget(self.file_label)
        layout.addLayout(header)

        split = QHBoxLayout()

        # --- sidebar: saved notes ---
        side = QWidget()
        side.setFixedWidth(220)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(0, 0, 8, 0)

        side_label = QLabel("Saved notes")
        side_label.setStyleSheet("color: #aaaaaa; font-weight: bold;")
        side_layout.addWidget(side_label)

        self.note_list = QListWidget()
        self.note_list.itemClicked.connect(self.load_note)
        side_layout.addWidget(self.note_list)

        new_btn = QPushButton("New Note")
        new_btn.clicked.connect(self.new_note)
        delete_btn = QPushButton("Delete Note")
        delete_btn.clicked.connect(self.delete_selected)
        side_layout.addWidget(new_btn)
        side_layout.addWidget(delete_btn)
        self.status = QLabel("")
        self.status.setStyleSheet("color: #ef4444;")
        side_layout.addWidget(self.status)

        split.addWidget(side)

        # --- editor ---
        self.editor = QTextEdit()
        split.addWidget(self.editor, 1)
        layout.addLayout(split, 1)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self.save_note)
        buttons.addWidget(save_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

    def main(self):
        self.refresh_list()

    # ---------- file list ----------

    def sandbox_path(self, name: str) -> str:
        return os.path.join(self.bridge.sandbox_path, name)

    def refresh_list(self):
        self.note_list.clear()
        try:
            files = self.bridge.list_app_files()
        except Exception:
            files = []
            if os.path.isdir(self.bridge.sandbox_path):
                files = [f for f in os.listdir(self.bridge.sandbox_path)
                         if os.path.isfile(self.sandbox_path(f))]
        notes = sorted(f for f in files if f.lower().endswith(".txt"))
        for name in notes:
            self.note_list.addItem(QListWidgetItem(name))
        if not notes:
            self.note_list.addItem("No notes yet")
            self.note_list.setEnabled(False)
        else:
            self.note_list.setEnabled(True)
        # keep current selection if still exists
        if self.current_file and self.current_file in notes:
            row = notes.index(self.current_file)
            self.note_list.setCurrentRow(row)

    # ---------- actions ----------

    def new_note(self):
        default = "untitled_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        name, ok = QInputDialog.getText(
            self, "New note", "Note name:", text=default)
        name = (name or "").strip()
        if not ok or not name:
            return
        if not name.lower().endswith(".txt"):
            name += ".txt"
        self.current_file = name
        self.editor.clear()
        self.file_label.setText(name)
        self.status.setText("")
        self.refresh_list()

    def load_note(self, item):
        name = item.text()
        if name == "No notes yet":
            return
        try:
            content = self.bridge.read_file(self.sandbox_path(name))
        except Exception as e:
            self.status.setText(f"Failed to open {name}: {e}")
            return
        self.current_file = name
        self.editor.setPlainText(content)
        self.file_label.setText(name)
        self.status.setText("")

    def save_note(self):
        if not self.current_file:
            self.new_note()
            if not self.current_file:
                return
        try:
            self.bridge.write_file(self.sandbox_path(self.current_file),
                                   self.editor.toPlainText())
            self.status.setText("")
            self.file_label.setText(self.current_file)
            self.refresh_list()
        except Exception as e:
            self.status.setText(f"Save error: {e}")

    def delete_selected(self):
        if not self.current_file:
            if not self.note_list.selectedItems():
                self.status.setText("No note selected.")
                return
            self.current_file = self.note_list.selectedItems()[0].text()
        name = self.current_file
        if not QMessageBox.question(
            self, "Delete", f"Delete note '{name}'?",
        ) == QMessageBox.StandardButton.Yes:
            return
        try:
            self.bridge.delete_file(self.sandbox_path(name))
        except Exception as e:
            self.status.setText(f"Could not delete: {e}")
            return
        self.current_file = None
        self.editor.clear()
        self.file_label.setText("No note open")
        self.status.setText("")
        self.refresh_list()