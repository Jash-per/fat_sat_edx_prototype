# calibration.py

from enum import Enum
from typing import Union
from util.functions import copy_enum

from models.state_machine import StateDescriptor, TransitionsDescriptor, StateEventHandler
from models.state_machine import StandardStates

from PySide6.QtCore import Slot
from PySide6.QtStateMachine import QState


class CalibrationStates(Enum):
    IDLE = StateDescriptor('IDLE', TransitionsDescriptor('INITIALZING', optional=['STOPPING', 'ERROR']), initial=True)
    INITIALZING = StateDescriptor('INITIALZING', TransitionsDescriptor('CALIBRATION_1', optional=['ERROR']))
    CALIBRATION_1 = StateDescriptor('CALIBRATION_1', TransitionsDescriptor('CALIBRATION_2', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    CALIBRATION_2 = StateDescriptor('CALIBRATION_2', TransitionsDescriptor('CALIBRATION_3', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    CALIBRATION_3 = StateDescriptor('CALIBRATION_3', TransitionsDescriptor('CALIBRATION_4', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    CALIBRATION_4 = StateDescriptor('CALIBRATION_4', TransitionsDescriptor('CALIBRATION_5', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    CALIBRATION_5 = StateDescriptor('CALIBRATION_5', TransitionsDescriptor('CALIBRATION_6', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    CALIBRATION_6 = StateDescriptor('CALIBRATION_6', TransitionsDescriptor('VERYFING', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    VERYFING = StateDescriptor('VERYFING', TransitionsDescriptor('COMPLETING', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    COMPLETING = StateDescriptor('COMPLETING', TransitionsDescriptor('COMPLETED', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'CalibrationProcedure'))
    COMPLETED = StateDescriptor('COMPLETED', final=True)
    # Controls
    STOPPING = StateDescriptor('STOPPING', TransitionsDescriptor('STOPPED', optional=['ERROR']))
    STOPPED = StateDescriptor('STOPPED', TransitionsDescriptor('IDLE', optional=['ERROR']))
    ABORTING = StateDescriptor('ABORTING', TransitionsDescriptor('ABORTED', optional=['ERROR']))
    ABORTED = StateDescriptor('ABORTED', TransitionsDescriptor('RESETTING', optional=['ERROR']))
    RESETTING = StateDescriptor('RESETTING', TransitionsDescriptor('IDLE', optional=['ERROR']))
    ERROR = StateDescriptor('ERROR', TransitionsDescriptor('RESETTING', optional=['ERROR']))


class CalibrationModel(StateEventHandler):

    state_log = ""

    def __init__(self):
        self.state_log = ""

    @Slot()
    def state_entered(self, state: QState, state_enum: Union[CalibrationStates, StandardStates]):
        print(f"[{__class__.__name__}] Entered new state: {state_enum.value.parent}.{state_enum}.")
        self.state_log += f"{state_enum.value.parent}.{state_enum}\n"

    @Slot()
    def machine_finished(self):
        ...
