import random

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Stonks"
    app_id = "stonks"
    app_version = "1.0.0"
    app_description = "Buy and sell virtual stocks to grow your gBalance."

    FIELD_KEY = "stonks_portfolio"

    STOCKS = [
        {"name": "GNET", "price": 10.0},
        {"name": "TOCTX", "price": 5.0},
        {"name": "MONEY", "price": 20.0},
    ]

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.prices = {s["name"]: s["price"] for s in self.STOCKS}
        self.holdings = {}  # name -> shares

        self.setMinimumSize(420, 440)
        self.setWindowTitle("Stonks")

        layout = QVBoxLayout(self)

        self.balance_label = QLabel("")
        self.balance_label.setStyleSheet("color: #3b82f6; font-size: 15px; font-weight: bold;")
        layout.addWidget(self.balance_label)

        self.portfolio_label = QLabel("")
        self.portfolio_label.setStyleSheet("color: #dddddd;")
        layout.addWidget(self.portfolio_label)

        self.stock_list = QListWidget()
        self.stock_list.itemClicked.connect(lambda _it: None)
        layout.addWidget(self.stock_list, 1)

        trade_row = QHBoxLayout()
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.0, 5000.0)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(5.0)
        buy_btn = QPushButton("Buy")
        buy_btn.clicked.connect(self.buy)
        sell_btn = QPushButton("Sell")
        sell_btn.clicked.connect(self.sell)
        trade_row.addWidget(self.amount_spin)
        trade_row.addWidget(buy_btn)
        trade_row.addWidget(sell_btn)
        layout.addLayout(trade_row)

        self.hint = QLabel("Select a stock, enter an amount, then Buy or Sell.")
        self.hint.setStyleSheet("color: #888888;")
        layout.addWidget(self.hint)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(self.status)

        self.ticker = QTimer(self)
        self.ticker.timeout.connect(self.tick)
        self.ticker.start(1500)

    def main(self):
        try:
            stored = self.bridge.get_user_field(self.FIELD_KEY)
            if isinstance(stored, dict):
                self.holdings = stored
        except Exception:
            pass
        self.refresh()

    def current_holding(self):
        it = self.stock_list.currentItem()
        if it is None:
            return None
        text = it.text().strip()
        # line format: "NAME  $12.34  (x shares = $y)"
        name = text.split()[0]
        return name if name in self.prices else None

    def value_of(self, name):
        return self.holdings.get(name, 0.0) * self.prices.get(name, 0.0)

    def refresh(self):
        bal = 0.0
        try:
            bal = self.bridge.get_gbalance()
        except Exception:
            pass
        self.balance_label.setText(f"gBalance: ${bal:.2f}")

        self.stock_list.clear()
        for name, price in self.prices.items():
            shares = self.holdings.get(name, 0)
            self.stock_list.addItem(
                QListWidgetItem(f"{name}  ${price:6.2f}   ({shares} shares = ${price*shares:.2f})")
            )
        self.update_portfolio(bal)

    def update_portfolio(self, bal=None):
        if bal is None:
            try:
                bal = self.bridge.get_gbalance()
            except Exception:
                bal = 0.0
        total = bal
        for name, price in self.prices.items():
            total += self.value_of(name, price)
        self.portfolio_label.setText(f"Total value (cash + stocks): ${total:.2f}")

    def value_of(self, name, price):
        return self.holdings.get(name, 0.0) * price

    def tick(self):
        for name, price in self.prices.items():
            change = random.uniform(-0.04, 0.04)  # +/-4%
            new_price = round(max(0.1, price * (1 + change)), 2)
            self.prices[name] = new_price
        self.refresh()

    def save_holdings(self):
        try:
            self.bridge.set_user_field(self.FIELD_KEY, self.holdings)
        except Exception:
            pass

    def buy(self):
        name = self.current_holding()
        if not name:
            self.status.setText("Select a stock first.")
            return
        amount = float(self.amount_spin.value())
        price = self.prices[name]
        if price <= 0:
            return
        shares = round(amount / price, 4)
        try:
            self.bridge.spend_gbalance(amount)
        except Exception as e:
            self.status.setText(f"Buy failed: {str(e)[:60]}")
            return
        self.holdings[name] = round(self.holdings.get(name, 0.0) + shares, 4)
        self.save_holdings()
        self.hint.setText(f"Bought {shares} shares of {name} at ${price:.2f}.")
        self.refresh()

    def sell(self):
        name = self.current_holding()
        if not name:
            self.status.setText("Select a stock first.")
            return
        shares = self.holdings.get(name, 0.0)
        if shares <= 0:
            self.status.setText(f"You own no {name}.")
            return
        price = self.prices[name]
        proceeds = round(shares * price, 2)
        amount = float(self.amount_spin.value())
        # sell all shares the amount represents, or all if they own less
        to_sell = min(shares, round(amount / price, 4))
        if to_sell <= 0:
            self.status.setText("Amount too small to sell.")
            return
        proceeds = round(to_sell * price, 2)
        try:
            self.bridge.award_gbalance(proceeds)
        except Exception as e:
            self.status.setText(f"Sell failed: {str(e)[:60]}")
            return
        self.holdings[name] = round(shares - to_sell, 4)
        if self.holdings[name] <= 0:
            del self.holdings[name]
        self.save_holdings()
        self.hint.setText(f"Sold {to_sell} shares of {name} for ${proceeds:.2f}.")
        self.refresh()