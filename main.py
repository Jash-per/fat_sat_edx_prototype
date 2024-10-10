# main.py

import sys
# from PySide6 import QtCore as QtCore
from PySide6 import QtWidgets as QtWidgets

if __name__ == "__main__":
    app = QtWidgets.QApplication()
    window = QtWidgets.QMainWindow()
    button = QtWidgets.QPushButton("close")
    button.clicked.connect(app.exit)
    central_widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(central_widget)
    layout.addWidget(button)
    window.setCentralWidget(central_widget)
    window.show()
    sys.exit(app.exec())
