# view.py
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QDialog,
)
from PySide6.QtCore import QSize


class WindowHelp(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setMinimumSize(QSize(400, 300))
        layout = QHBoxLayout()
        self.text = QLabel("Hi")
        layout.addWidget(self.text)
        self.setLayout(layout)
