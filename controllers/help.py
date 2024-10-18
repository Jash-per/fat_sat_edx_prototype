# help.py
from views.help import WindowHelp


class ControllerHelp:
    def __init__(self, parent=None):
        self.view = WindowHelp(parent)

    def show(self):
        self.view.show()
