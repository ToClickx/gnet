import time
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Stopwatch"
    app_id = "stopwatch"
    app_version = "1.0.0"
    app_description = "A lap-capable stopwatch."

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.running = False
        self.start_time = 0.0
        self.elapsed = 0.0
        self.laps = []

        self.setMinimumSize(260, 420)
        self.setWindowTitle("Stopwatch")

        layout = QVBoxLayout(self)

        self.time_label = QLabel("00:00.0")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Fira Code", 34))
        self.time_label.setStyleSheet("color: #3b82f6;")
        layout.addWidget(self.time_label)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.toggle)
        lap_btn = QPushButton("Lap")
        lap_btn.setFixedHeight(40)
        lap_btn.clicked.connect(self.lap)
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedHeight(40)
        reset_btn.clicked.connect(self.reset)
        controls.addWidget(self.start_btn)
        controls.addWidget(lap_btn)
        controls.addWidget(reset_btn)
        layout.addLayout(controls)

        self.lap_widget = QListWidget()
        layout.addWidget(self.lap_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(100)

    def toggle(self):
        if self.running:
            self.elapsed += time.time() - self.start_time
            self.running = False
            self.start_btn.setText("Start")
        else:
            self.start_time = time.time()
            self.running = True
            self.start_btn.setText("Pause")

    def lap(self):
        if not self.running:
            return
        self.laps.append(self.current_time())
        self.lap_widget.addItem(
            QListWidgetItem(f"Lap {len(self.laps)}: {self.format_time(self.laps[-1])}")
        )

    def reset(self):
        self.running = False
        self.elapsed = 0.0
        self.start_time = 0.0
        self.laps = []
        self.lap_widget.clear()
        self.time_label.setText("00:00.0")
        self.start_btn.setText("Start")

    def current_time(self):
        return self.elapsed + (time.time() - self.start_time) if self.running else self.elapsed

    @staticmethod
    def format_time(seconds):
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:04.1f}"

    def update_display(self):
        self.time_label.setText(self.format_time(self.current_time()))