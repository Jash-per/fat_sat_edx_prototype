# controller.py
from PySide6.QtCore import Slot
from PySide6.QtStateMachine import QState
from controllers.help import ControllerHelp
from models.state_machine import StateMachineModel, StandardStates, StateEventHandler
from models.calibration import CalibrationStates, CalibrationModel
from views.main import MainWindow


class ControllerMain(StateEventHandler):
    def __init__(self):
        super().__init__()
        self.calibration_model = CalibrationModel()
        self.statemachine = StateMachineModel(parents=[self.calibration_model, self], states_enum=CalibrationStates)
        self.view_main = MainWindow(self, self.calibration_model, statemachine=self.statemachine)

    @Slot()
    def trigger_prev_state(self):
        self.statemachine.to_previous.emit()

    @Slot()
    def trigger_next_state(self):
        self.statemachine.to_next.emit()

    @Slot()
    def trigger_stop(self):
        self.statemachine.to_stopping.emit()

    @Slot()
    def trigger_error(self):
        self.statemachine.to_error.emit()

    def show(self):
        self.view_main.show()

    @Slot()
    def state_entered(self, state: QState, state_enum: StandardStates):
        print(f"[{__class__.__name__}] Entered new state: {state_enum.value.parent}.{state_enum}.")
        self.view_main.update_state(state_enum)

    @Slot()
    def machine_finished(self):
        ...

    @Slot()
    def save_file(self):
        print("Saved")

    @Slot()
    def open_help(self) -> None:
        help_controller = ControllerHelp(parent=self.view_main)
        help_controller.show()

    @Slot()
    def close_main_window(self) -> None:
        self.view_main.close()
