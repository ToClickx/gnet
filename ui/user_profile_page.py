from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt


class UserProfilePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = QLabel("Profile")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # ---------- auth card ----------
        self.auth_card = QGroupBox("Log In or Register")
        self.auth_card.setStyleSheet("""
            QGroupBox { color: #dddddd; font-weight: bold; border: 1px solid #3b82f6;
                        border-radius: 12px; margin-top: 10px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        auth_form = QFormLayout(self.auth_card)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        auth_form.addRow("Username:", self.username_edit)
        auth_form.addRow("Password:", self.password_edit)

        auth_btns = QHBoxLayout()
        login_btn = QPushButton("Log In")
        login_btn.setFixedSize(120, 36)
        login_btn.clicked.connect(self.login)
        register_btn = QPushButton("Register")
        register_btn.setFixedSize(120, 36)
        register_btn.clicked.connect(self.register)
        auth_btns.addWidget(login_btn)
        auth_btns.addWidget(register_btn)
        auth_btns.addStretch()
        auth_form.addRow(auth_btns)

        self.auth_status = QLabel("")
        self.auth_status.setStyleSheet("color: #ef4444;")
        auth_form.addRow(self.auth_status)

        # ---------- user info stack ----------
        self.info = QWidget()
        info_layout = QVBoxLayout(self.info)

        info_card = QGroupBox("Your Account")
        info_card.setStyleSheet("""
            QGroupBox { color: #dddddd; font-weight: bold; border: 1px solid #3b82f6;
                        border-radius: 12px; margin-top: 10px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        layoutF = QFormLayout(info_card)
        self.username_label = QLabel("")
        self.balance_label = QLabel("")
        self.cards_label = QLabel("")
        layoutF.addRow("Username:", self.username_label)
        layoutF.addRow("gBalance:", self.balance_label)
        layoutF.addRow("Debit cards:", self.cards_label)
        info_layout.addWidget(info_card)

        txn_group = QGroupBox("Recent Transactions")
        txn_group.setStyleSheet("""
            QGroupBox { color: #dddddd; font-weight: bold; border: 1px solid #444444;
                        border-radius: 12px; margin-top: 10px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)
        txn_layout = QVBoxLayout(txn_group)
        self.txn_list = QListWidget()
        self.txn_list.setStyleSheet("background: #2a2a2a; border-radius: 10px;")
        txn_layout.addWidget(self.txn_list)
        info_layout.addWidget(txn_group)

        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedSize(120, 36)
        logout_btn.clicked.connect(self.logout)
        info_layout.addWidget(logout_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        info_layout.addStretch()

        layout.addWidget(self.auth_card)
        layout.addWidget(self.info)
        layout.addStretch()

    def refresh(self):
        user = self.main_window.user_manager.current_user()
        if user:
            self.auth_card.hide()
            self.info.show()
            self.username_label.setText(user.username)
            self.balance_label.setText(f"${user.gBalance:.2f}")
            self.cards_label.setText(str(len(user.debit_cards)))

            self.txn_list.clear()
            recent = list(reversed(user.transaction_log[-20:]))
            if recent:
                for t in recent:
                    ts = t.get("timestamp", "?")
                    self.txn_list.addItem(
                        QListWidgetItem(f"[{ts}]  {t.get('type', '')}  ${t.get('amount', 0)}")
                    )
            else:
                self.txn_list.addItem("No transactions yet.")
        else:
            self.auth_card.show()
            self.info.hide()
            self.auth_status.setText("")

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        try:
            self.main_window.user_manager.login(username, password)
        except ValueError as e:
            self.auth_status.setText(str(e))
            return
        self.username_edit.clear()
        self.password_edit.clear()
        self.main_window.on_user_changed()

    def register(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self.auth_status.setText("Username and password required.")
            return
        try:
            self.main_window.user_manager.create_user(username, password)
            self.main_window.user_manager.login(username, password)
        except ValueError as e:
            self.auth_status.setText(str(e))
            return
        self.username_edit.clear()
        self.password_edit.clear()
        self.main_window.on_user_changed()

    def logout(self):
        self.main_window.user_manager.logout()
        self.main_window.on_user_changed()