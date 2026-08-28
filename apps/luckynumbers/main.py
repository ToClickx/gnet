import random

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Lucky Numbers"
    app_id = "luckynumbers"
    app_version = "1.0.0"
    app_description = "Bet gBalance on a number 1-10 and win 5x your bet."

    FIELD_KEY = "luckynumbers_stats"

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.stats = {"wins": 0, "losses": 0}

        self.setMinimumSize(320, 380)
        self.setWindowTitle("Lucky Numbers")

        layout = QVBoxLayout(self)

        self.balance_label = QLabel("")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.balance_label.setStyleSheet("color: #3b82f6; font-size: 15px; font-weight: bold;")
        layout.addWidget(self.balance_label)

        title = QLabel("Pick a number 1 - 10")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px;")
        layout.addWidget(title)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        layout.addWidget(self.result_label)

        grid = QGridLayout()
        for i in range(1, 11):
            btn = QPushButton(str(i))
            btn.setFixedSize(46, 46)
            btn.setFont(QFont("Fira Code", 14))
            btn.clicked.connect(lambda checked=False, n=i: self.play(n))
            grid.addWidget(btn, (i - 1) // 5, (i - 1) % 5)
        layout.addLayout(grid)

        bet_row = QHBoxLayout()
        bet_row.addWidget(QLabel("Bet:"))
        self.bet_spin = QDoubleSpinBox()
        self.bet_spin.setRange(0.0, 500.0)
        self.bet_spin.setDecimals(2)
        self.bet_spin.setValue(1.0)
        self.bet_spin.setSingleStep(0.5)
        bet_row.addWidget(self.bet_spin, 1)
        layout.addLayout(bet_row)

        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.stats_label)

    def main(self):
        try:
            stored = self.bridge.get_user_field(self.FIELD_KEY)
            if isinstance(stored, dict):
                self.stats = stored
        except Exception:
            pass
        self.update_balance()
        self.update_stats_label()

    def update_balance(self):
        try:
            self.balance_label.setText(f"gBalance: ${self.bridge.get_gbalance():.2f}")
        except Exception:
            self.balance_label.setText("gBalance: --")

    def play(self, guess: int):
        bet = float(self.bet_spin.value())
        if bet <= 0:
            self.result_label.setText("Enter a bet amount first.")
            return
        try:
            self.bridge.spend_gbalance(bet)
        except Exception as e:
            self.result_label.setText(f"Could not place bet: {str(e)[:60]}")
            return

        roll = random.randint(1, 10)
        hit = roll == guess
        if hit:
            payout = bet * 5
            try:
                self.bridge.award_gbalance(payout)
            except Exception as e:
                self.result_label.setText(f"Payout failed: {str(e)[:60]}")
                return
            self.stats["wins"] += 1
            self.result_label.setText(
                f"Rolled {roll}! You won ${payout:.2f}!"
            )
        else:
            self.stats["losses"] += 1
            self.result_label.setText(f"Rolled {roll}... lost ${bet:.2f}.")
        self.save_stats()
        self.update_stats_label()
        self.update_balance()

    def save_stats(self):
        try:
            self.bridge.set_user_field(self.FIELD_KEY, self.stats)
        except Exception:
            pass

    def update_stats_label(self):
        w = self.stats.get("wins", 0)
        l = self.stats.get("losses", 0)
        self.stats_label.setText(f"W {w}   L {l}")