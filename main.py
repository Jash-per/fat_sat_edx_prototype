# main.py
import sys
from PySide6.QtWidgets import QApplication
from controllers.main import ControllerMain


class StatefulApplication(QApplication):
    def __init__(self):
        super().__init__()
        self.controller = ControllerMain()
        self.controller.show()


if __name__ == "__main__":
    app = StatefulApplication()
    sys.exit(app.exec())
