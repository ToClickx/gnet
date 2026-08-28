from PyQt6.QtWidgets import QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from sdk.app_base import GNetAppBase


class App(GNetAppBase):
    app_name = "Calculator"
    app_id = "calculator"
    app_version = "1.0.0"
    app_description = "A simple four-function calculator."

    def __init__(self, bridge, parent=None):
        super().__init__(bridge, parent)
        self.expression = ""

        self.setMinimumSize(320, 460)
        self.setWindowTitle("Calculator")

        layout = QVBoxLayout(self)

        self.display = QLineEdit("0")
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setReadOnly(True)
        self.display.setFixedHeight(64)
        f = QFont("Fira Code", 20)
        f.setBold(True)
        self.display.setFont(f)
        layout.addWidget(self.display)

        grid = QGridLayout()
        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2), ("/", 0, 3),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2), ("*", 1, 3),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2), ("-", 2, 3),
            ("C", 3, 0), ("0", 3, 1), (".", 3, 2), ("+", 3, 3),
        ]
        for label, row, col in buttons:
            btn = QPushButton(label)
            btn.setFixedHeight(56)
            btn.setFont(QFont("Fira Code", 16))
            btn.clicked.connect(lambda checked=False, t=label: self.press(t))
            grid.addWidget(btn, row, col)

        eq = QPushButton("=")
        eq.setFixedHeight(56)
        eq.setFont(QFont("Fira Code", 18))
        eq.clicked.connect(self.calculate)
        grid.addWidget(eq, 4, 0, 1, 4)

        layout.addLayout(grid)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color: #888888;")
        layout.addWidget(self.status)

    def press(self, token: str):
        if token == "C":
            self.expression = ""
            self.display.setText("0")
            self.status.setText("")
            return
        if token in "+-*/":
            self.expression += f" {token} "
        else:
            self.expression += token
        self.display.setText(self.expression.strip())

    def calculate(self):
        try:
            result = eval(self.expression, {"__builtins__": {}}, {})
            self.display.setText(str(result))
            self.expression = str(result)
            self.status.setText("")
        except Exception:
            self.status.setText("Invalid expression")
            self.display.setText("0")
            self.expression = ""