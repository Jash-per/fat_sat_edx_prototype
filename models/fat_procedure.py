# calibration.py

from enum import Enum
from typing import Union
from util.functions import copy_enum

from models.state_machine import StateMachineModel, StateDescriptor, TransitionsDescriptor, StateEventHandler
from models.state_machine import StandardStates

from PySide6.QtCore import Slot
from PySide6.QtStateMachine import QState


class FATProcedureStates(Enum):
    IDLE = StateDescriptor('IDLE', TransitionsDescriptor('INITIALZING', optional=['STOPPING', 'ERROR'], prev_state='IDLE'), initial=True)
    INITIALZING = StateDescriptor('INITIALZING', TransitionsDescriptor(('FAT_PROCEDURE_1', 'FAT_PROCEDURE_2', 'FAT_PROCEDURE_3'), optional=['ERROR']))
    FAT_PROCEDURE_1 = StateDescriptor('FAT_PROCEDURE_1', TransitionsDescriptor('FAT_PROCEDURE_2', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatSubProcedureStates_1'))
    FAT_PROCEDURE_2 = StateDescriptor('FAT_PROCEDURE_2', TransitionsDescriptor('FAT_PROCEDURE_3', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatSubProcedureStates_2'))
    FAT_PROCEDURE_3 = StateDescriptor('FAT_PROCEDURE_3', TransitionsDescriptor('FAT_PROCEDURE_4', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatSubProcedureStates_3'))
    FAT_PROCEDURE_4 = StateDescriptor('FAT_PROCEDURE_4', TransitionsDescriptor('FAT_PROCEDURE_5', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatSubProcedureStates_4'))
    FAT_PROCEDURE_5 = StateDescriptor('FAT_PROCEDURE_5', TransitionsDescriptor('FAT_PROCEDURE_6', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatSubProcedureStates_5'))
    FAT_PROCEDURE_6 = StateDescriptor('FAT_PROCEDURE_6', TransitionsDescriptor('VERYFING', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatSubProcedureStates_6'))
    VERYFING = StateDescriptor('VERYFING', TransitionsDescriptor('COMPLETING', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatVerifyingStates'))
    COMPLETING = StateDescriptor('COMPLETING', TransitionsDescriptor('COMPLETED', optional=['ERROR']), sub_states=copy_enum(StandardStates, 'FatCompletingStates'))
    COMPLETED = StateDescriptor('COMPLETED', final=True)
    # Controls don't allow previous transitions...
    STOPPING = StateDescriptor('STOPPING', TransitionsDescriptor('STOPPED', optional=['ERROR'], prev_state='STOPPING'))
    STOPPED = StateDescriptor('STOPPED', TransitionsDescriptor('IDLE', optional=['ERROR']))
    ABORTING = StateDescriptor('ABORTING', TransitionsDescriptor('ABORTED', optional=['ERROR'], prev_state='ABORTING'))
    ABORTED = StateDescriptor('ABORTED', TransitionsDescriptor('RESETTING', optional=['ERROR']))
    RESETTING = StateDescriptor('RESETTING', TransitionsDescriptor('IDLE', optional=['ERROR'], prev_state='RESETTING'))
    ERROR = StateDescriptor('ERROR', TransitionsDescriptor('RESETTING', optional=['ERROR'], prev_state='ERROR'))


class FATProdecureSuperStates(Enum):
    IDLE = StateDescriptor('IDLE', TransitionsDescriptor('STARTING', optional=['STOPPING', 'ERROR'], prev_state='IDLE'), initial=True)
    STARTING = StateDescriptor('STARTING', TransitionsDescriptor('EXECUTE', optional=['STOPPING', 'ERROR']))
    EXECUTE = StateDescriptor('EXECUTE', TransitionsDescriptor('COMPLETE', optional=['STOPPING', 'ERROR']), sub_states=FATProcedureStates)
    COMPLETE = StateDescriptor('COMPLETE', final=False)
    # Controls don't allow previous transitions...
    STOPPING = StateDescriptor('STOPPING', TransitionsDescriptor('STOPPED', optional=['ERROR'], prev_state='STOPPING'))
    STOPPED = StateDescriptor('STOPPED', TransitionsDescriptor('IDLE', optional=['ERROR']))
    ABORTING = StateDescriptor('ABORTING', TransitionsDescriptor('ABORTED', optional=['ERROR'], prev_state='ABORTING'))
    ABORTED = StateDescriptor('ABORTED', TransitionsDescriptor('RESETTING', optional=['ERROR']))
    RESETTING = StateDescriptor('RESETTING', TransitionsDescriptor('IDLE', optional=['ERROR'], prev_state='RESETTING'))
    ERROR = StateDescriptor('ERROR', TransitionsDescriptor('RESETTING', optional=['ERROR'], prev_state='IDLE'))


class FATProdedureModel(StateEventHandler):

    state_log = ""
    state_machine: StateMachineModel

    def __init__(self):
        self.state_log = ""
        self.statemachine: StateMachineModel = None

    @Slot()
    def state_entered(self, state: QState, state_enum: Union[FATProcedureStates, StandardStates]):
        print(f"[{__class__.__name__}] Entered new state: {state_enum.value.parent}.{state_enum}.")
        for state_enum in self.statemachine.current_state_tree:
            self.state_log += f"{state_enum.name}."
        self.state_log += "\n"

    @Slot()
    def machine_finished(self):
        ...
