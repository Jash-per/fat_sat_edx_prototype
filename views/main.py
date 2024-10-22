# view.py
from enum import Enum
from PySide6.QtStateMachine import QState
from models.state_machine import StateMachineModel
from PySide6.QtCore import QSize, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QStatusBar,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
    QTextEdit,
    QScrollArea
)


class MainWindow(QMainWindow):
    windowSize: QSize = QSize(800, 600)
    statemachine: StateMachineModel = None

    def __init__(self, controller, model, statemachine=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.model = model
        if statemachine is not None:
            self.statemachine = statemachine
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Stateful GUI application")
        self.setBaseSize(self.windowSize)
        self.setMinimumSize(self.windowSize)
        self.init_menu_bar()
        self.init_content()
        self.init_status_bar()

    def init_menu_bar(self):
        self.menu_bar = self.menuBar()
        menu_structure = {
            'File': ['New', 'Open', 'Save', 'Exit'],
            'Edit': ['Undo', 'Redo'],
            'Help': ['Welcome', ],
        }
        for menu_name, actions in menu_structure.items():
            attr_name_menu = f'menu_{menu_name.lower()}'
            setattr(self, attr_name_menu, self.menu_bar.addMenu(menu_name))
            menu: QMenu = getattr(self, attr_name_menu)
            for action_name in actions:
                attr_name_action = f'action_{action_name.lower()}'
                setattr(menu, attr_name_action, QAction(action_name))
                menu.addAction(getattr(menu, attr_name_action))

        self.menu_file.action_save.triggered.connect(self.controller.save_file)
        self.menu_file.action_exit.triggered.connect(self.controller.close_main_window)
        self.menu_help.action_welcome.triggered.connect(self.controller.open_help)

    def init_content(self) -> None:
        layout_text = QHBoxLayout()
        scroll_area = QScrollArea()
        self.text_edit = QTextEdit()
        # self.text_edit.setDisabled(True)
        self.text_edit.setPlainText(self.model.state_log)
        scroll_area.setWidget(self.text_edit)
        scroll_area.setWidgetResizable(True)
        layout_text.addWidget(scroll_area)

        layout_form = QHBoxLayout()
        self.btn_prev_state = QPushButton("Previous state")
        self.btn_nxt_state = QPushButton("Next state")
        self.btn_to_stop = QPushButton("Stop")
        self.btn_to_error = QPushButton("Error")
        layout_form.addWidget(self.btn_prev_state)
        layout_form.addWidget(self.btn_nxt_state)
        layout_form.addWidget(self.btn_to_stop)
        layout_form.addWidget(self.btn_to_error)

        self.btn_prev_state.clicked.connect(self.controller.trigger_prev_state)
        self.btn_nxt_state.clicked.connect(self.controller.trigger_next_state)
        self.btn_to_stop.clicked.connect(self.controller.trigger_stop)
        self.btn_to_error.clicked.connect(self.controller.trigger_error)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_text)
        layout_main.addLayout(layout_form)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout_main)
        self.setCentralWidget(self.central_widget)

    def init_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        state_lbl = QLabel("State-Machine state:")
        state_lbl.setStyleSheet("font-weight: bold;")
        self.label_state = QLabel("")
        self.status_bar.addPermanentWidget(state_lbl)
        self.status_bar.addPermanentWidget(self.label_state)

    @Slot()
    def state_entered(self, state: QState, state_enum: Enum):
        self.text_edit.setText(self.model.state_log)
        self.label_state.setText(state_enum.name)

    def update_state(self, state: Enum) -> None:
        ...
        # self.text_edit.setPlainText(self.model.state_log)
        # if state.value.parent:
        #     self.label_state.setText(f'{state.value.parent.name}.{state.name}')
        # else:
        #     self.label_state.setText(f'{state.name}')
