import random

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDoubleSpinBox,
    QButtonGroup,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Coin Flip"
    app_id = "coinflip"
    app_version = "1.1.0"
    app_description = "Flip a virtual coin and bet on the outcome."

    FIELD_KEY = "coinflip_stats"

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.stats = {"wins": 0, "losses": 0}
        self.pick = "H"
        self.animating = False

        self.setMinimumSize(320, 360)
        self.setWindowTitle("Coin Flip")

        layout = QVBoxLayout(self)

        self.balance_label = QLabel("")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.balance_label.setStyleSheet("color: #3b82f6; font-size: 15px; font-weight: bold;")
        layout.addWidget(self.balance_label)

        self.coin_label = QLabel("?")
        self.coin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.coin_label.setFont(QFont("Fira Code", 90))
        self.coin_label.setStyleSheet("color: #dddddd;")
        layout.addWidget(self.coin_label)

        side_row = QHBoxLayout()
        self.heads_btn = QPushButton("Heads")
        self.heads_btn.setCheckable(True)
        self.heads_btn.setChecked(True)
        self.tails_btn = QPushButton("Tails")
        self.tails_btn.setCheckable(True)
        self.heads_btn.clicked.connect(lambda: self.set_pick("H"))
        self.tails_btn.clicked.connect(lambda: self.set_pick("T"))
        side_row.addWidget(self.heads_btn)
        side_row.addWidget(self.tails_btn)
        layout.addLayout(side_row)

        bet_row = QHBoxLayout()
        bet_row.addWidget(QLabel("Bet:"))
        self.bet_spin = QDoubleSpinBox()
        self.bet_spin.setRange(0.0, 1000.0)
        self.bet_spin.setDecimals(2)
        self.bet_spin.setValue(1.0)
        self.bet_spin.setSingleStep(0.5)
        bet_row.addWidget(self.bet_spin, 1)

        self.flip_btn = QPushButton("Flip")
        self.flip_btn.setFixedHeight(40)
        self.flip_btn.clicked.connect(self.flip)
        bet_row.addWidget(self.flip_btn)
        layout.addLayout(bet_row)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        layout.addWidget(self.result_label)

        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.stats_label)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)

    def main(self):
        self.load_stats()
        self.update_balance()

    def set_pick(self, pick):
        self.pick = pick
        self.heads_btn.setChecked(pick == "H")
        self.tails_btn.setChecked(pick == "T")

    # ---------- economy ----------

    def update_balance(self):
        try:
            bal = self.bridge.get_gbalance()
        except Exception:
            bal = 0.0
        self.balance_label.setText(f"gBalance: ${bal:.2f}")

    def load_stats(self):
        try:
            stored = self.bridge.get_user_field(self.FIELD_KEY)
            if isinstance(stored, dict):
                self.stats = stored
        except Exception:
            self.stats = {"wins": 0, "losses": 0}
        self.render_stats()

    def render_stats(self):
        w = self.stats.get("wins", 0)
        l = self.stats.get("losses", 0)
        self.stats_label.setText(f"W {w}   L {l}")

    def save_stats(self):
        try:
            self.bridge.set_user_field(self.FIELD_KEY, self.stats)
        except Exception:
            pass

    # ---------- game ----------

    def flip(self):
        if self.animating:
            return
        self.animating = True
        self.anim_count = 0
        self.anim_timer.start(60)

    def animate(self):
        self.coin_label.setText(random.choice(["H", "T"]))
        self.anim_count += 1
        if self.anim_count >= 8:
            self.anim_timer.stop()
            self.animating = False
            self.resolve()

    def resolve(self):
        result = random.choice(["H", "T"])
        self.coin_label.setText(result)
        won = result == self.pick
        bet = float(self.bet_spin.value())
        name = "Heads" if result == "H" else "Tails"

        if bet > 0:
            if won:
                try:
                    self.bridge.spend_gbalance(bet)
                    self.bridge.award_gbalance(bet * 2)
                    payout = bet
                except Exception as e:
                    self.result_label.setText(f"Bet failed: {str(e)[:60]}")
                    return
                self.stats["wins"] += 1
                self.result_label.setText(
                    f"{name} - You win ${payout:.2f}!"
                )
            else:
                try:
                    self.bridge.spend_gbalance(bet)
                except Exception as e:
                    self.result_label.setText(f"Bet failed: {str(e)[:60]}")
                    return
                self.stats["losses"] += 1
                self.result_label.setText(f"{name} - You lose ${bet:.2f}.")
        else:
            self.result_label.setText(name + "!")

        self.save_stats()
        self.update_stats()
        self.update_balance()

    def update_stats(self):
        w = self.stats.get("wins", 0)
        l = self.stats.get("losses", 0)
        self.stats_label.setText(f"W {w}   L {l}")