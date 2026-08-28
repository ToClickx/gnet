import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE_QSS = os.path.join(BASE_DIR, "style.qss")
with open(STYLE_QSS, encoding="utf-8") as _f:
    style = _f.read()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gNet 2")
        self.setMinimumSize(1200, 800)
        
        # Set up main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #2a2a2a; border-right: 2px solid #3b82f6;")
        
        # Add navigation buttons
        nav_layout = QVBoxLayout(sidebar)
        nav_buttons = [
            ("Home", "home"),
            ("Apps", "apps"),
            ("Settings", "settings"),
            ("Profile", "profile")
        ]
        
        for text, icon in nav_buttons:
            btn = QPushButton(text)
            btn.setFixedSize(200, 50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            nav_layout.addWidget(btn)
        
        # Create content area
        content_area = QWidget()
        content_area.setStyleSheet("background-color: #1e1e1e;")
        content_layout = QVBoxLayout(content_area)
        
        # Add welcome message
        welcome_label = QLabel("Welcome to gNet 2")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #dddddd;
                padding: 50px;
            }
        """)
        content_layout.addWidget(welcome_label)
        
        # Add layouts to main layout
        layout.addWidget(sidebar)
        layout.addWidget(content_area)
        
        # Apply custom style
        self.setStyleSheet(style)