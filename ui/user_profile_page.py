from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem, QCheckBox,
)
from PyQt6.QtCore import Qt

import core.session as session


class UserProfilePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.user_manager = main_window.user_manager

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

        self.remember_check = QCheckBox("Remember me")
        auth_form.addRow(self.remember_check)

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

        add_card_btn = QPushButton("Add Debit Card")
        add_card_btn.setFixedWidth(140)
        add_card_btn.clicked.connect(self.add_debit_card)
        layoutF.addRow(add_card_btn)

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
            cards = user.debit_cards
            if cards:
                names = ", ".join(
                    c["name"] if isinstance(c, dict) else str(c)
                    for c in cards.values()
                )
                self.cards_label.setText(f"{len(cards)}: {names}")
            else:
                self.cards_label.setText("0")

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

    def add_debit_card(self):
        from PyQt6.QtWidgets import QInputDialog
        user = self.main_window.user_manager.current_user()
        if not user:
            return
        name, ok = QInputDialog.getText(self, "New debit card", "Card name:")
        name = (name or "").strip()
        if not ok or not name:
            return
        limit, ok = QInputDialog.getDouble(
            self, "New debit card", "Limit per time window (max spend):",
            100.0, 1.0, 100000.0, 2,
        )
        if not ok:
            return
        user.add_debit_card(
            f"card_{name.lower().replace(' ', '_')}", name,
            limit_amount=limit, limit_percent=1.0, time_window_seconds=86400,
        )
        self.refresh()

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        try:
            self.user_manager.login(username, password)
        except ValueError as e:
            self.auth_status.setText(str(e))
            return
        self._apply_remember(username)
        self.username_edit.clear()
        self.password_edit.clear()
        self.user_manager_changed()

    def register(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self.auth_status.setText("Username and password required.")
            return
        try:
            self.user_manager.create_user(username, password)
            self.user_manager.login(username, password)
        except ValueError as e:
            self.auth_status.setText(str(e))
            return
        self._apply_remember(username)
        self.username_edit.clear()
        self.password_edit.clear()
        self.user_manager_changed()

    def logout(self):
        session.clear()
        self.user_manager.logout()
        self.user_manager_changed()

    def _apply_remember(self, username):
        if self.remember_check.isChecked():
            session.save(username)
        else:
            session.clear()

    def user_manager_changed(self):
        self.main_window.on_user_changed()