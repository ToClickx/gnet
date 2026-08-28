import random
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Coin Flip"
    app_id = "coinflip"
    app_version = "1.0.0"
    app_description = "Flip a virtual coin and track the streak."

    FIELD_KEY = "coinflip_stats"

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.stats = {"flips": 0, "heads": 0, "tails": 0}
        self.animating = False

        self.setMinimumSize(300, 300)
        self.setWindowTitle("Coin Flip")

        layout = QVBoxLayout(self)

        self.coin_label = QLabel("?")
        self.coin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.coin_label.setFont(QFont("Fira Code", 90))
        self.coin_label.setStyleSheet("color: #dddddd;")
        layout.addWidget(self.coin_label)

        self.result_label = QLabel("Press Flip!")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        layout.addWidget(self.result_label)

        flip_btn = QPushButton("Flip")
        flip_btn.setFixedHeight(44)
        flip_btn.clicked.connect(self.flip)
        layout.addWidget(flip_btn)

        self.stats_label = QLabel("0 flips")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.stats_label)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)

    def main(self):
        self.load_stats()

    def load_stats(self):
        try:
            stored = self.bridge.get_user_field(self.FIELD_NAME)
            if isinstance(stored, dict):
                self.stats = stored
        except Exception:
            self.stats = {"flips": 0, "heads": 0, "tails": 0}
        self.update_stats()

    def save_stats(self):
        try:
            self.bridge.set_user_field(self.FIELD_NAME, self.stats)
        except Exception:
            pass

    def flip(self):
        if self.animating:
            return
        self.animating = True
        self.anim_count = 0
        self.anim_timer.start(60)

    def animate(self):
        side = random.choice(["H", "T"])
        self.coin_label.setText(side)
        self.anim_count += 1
        if self.anim_count >= 8:
            self.anim_timer.stop()
            self.animating = False
            result = random.choice(["H", "T"])
            self.coin_label.setText(result)
            name = "Heads" if result == "H" else "Tails"
            self.result_label.setText(name + "!")
            self.stats["flips"] += 1
            self.stats[name.lower()] += 1
            self.save_stats()
            self.update_stats()

    def update_stats(self):
        h = self.stats.get("heads", 0)
        t = self.stats.get("tails", 0)
        total = self.stats.get("flips", 0)
        if total:
            pct = round(h / total * 100)
            self.stats_label.setText(f"{total} flips  |  H {h}  T {t}  ({pct}%)")
        else:
            self.stats_label.setText("0 flips")