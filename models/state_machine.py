# model.py
from enum import Enum
from abc import ABC, abstractmethod
from functools import partial
from dataclasses import dataclass, field
from typing import Optional, Union, List, Any
from PySide6.QtCore import QObject, Signal
from PySide6.QtStateMachine import QStateMachine, QState, QFinalState
from util.functions import rdict


@dataclass(frozen=True)
class TransitionsDescriptor:
    next_state: str
    optional: list = field(default_factory=list)


@dataclass
class StateDescriptor:
    name: str
    transitions: Optional[TransitionsDescriptor] = None
    sub_states: Optional[Enum] = None
    initial: Optional[bool] = False
    final: Optional[bool] = False
    parent: Optional[Enum] = None


class StandardStates(Enum):
    IDLE = StateDescriptor('IDLE', TransitionsDescriptor('STARTING', optional=['STOPPING', 'ERROR']), initial=True)
    STARTING = StateDescriptor('STARTING', TransitionsDescriptor('EXECUTE', optional=['STOPPING', 'ERROR']))
    EXECUTE = StateDescriptor('EXECUTE', TransitionsDescriptor('COMPLETE', optional=['STOPPING', 'ERROR']))
    COMPLETE = StateDescriptor('COMPLETE', final=False)
    STOPPING = StateDescriptor('STOPPING', TransitionsDescriptor('STOPPED', optional=['ERROR']))
    STOPPED = StateDescriptor('STOPPED', TransitionsDescriptor('STARTING', optional=['ERROR']))
    ABORTING = StateDescriptor('ABORTING', TransitionsDescriptor('ABORTED', optional=['ERROR']))
    ABORTED = StateDescriptor('ABORTED', TransitionsDescriptor('RESETTING', optional=['ERROR']))
    RESETTING = StateDescriptor('RESETTING', TransitionsDescriptor('IDLE', optional=['ERROR']))
    ERROR = StateDescriptor('ERROR', TransitionsDescriptor('RESETTING', optional=['ERROR']))


class StateEventHandler(ABC):
    """
    class StateEventHandlers

    Can also bind event handlers to specific states (entered, finished, etc.) like this:

    def state_<state-name>_<event>(self):                  [NO CAPITALS]
        ...

    Or sub-states like this:
    def state_<state-name>__<sub-state-name>_<event>(self):      [NO CAPITALS!]
        ...

    eg.:
    def state_error_entered(self):
        ...
    """

    @abstractmethod
    def machine_finished(self):
        ...

    @abstractmethod
    def state_entered(self, state: QState, state_enum: Enum):
        ...

    def state_finished(self, state: QState, state_enum: Enum):
        ...

    def state_exited(self, state: QState, state_enum: Enum):
        ...


class StateMachineModel(QObject):
    """
    StateMachineModel(QObject)
    TODO: ADD DOCSTRING
    """

    # region Public:
    to_previous = Signal()
    to_next = Signal()  # Default signals
    to_error = Signal()  # Default signals
    to_stopping = Signal()  # Default signals
    skip = Signal()

    def __init__(self, parents: Union[Any, List, None] = None, states_enum: Optional[Enum] = None) -> None:
        super().__init__()
        if parents is not None and type(parents) is not list:
            self._parents = [parents]
        else:
            self._parents = parents

        if states_enum is None:
            self._states_enum = self.__default_states_enum
        else:
            self._states_enum = states_enum

        self._machine = QStateMachine()
        self._states = rdict()

        for state_enum in self._states_enum:
            state = self._states[state_enum] = self._create_state(self._machine, state_enum)
            if not state_enum.value.sub_states:
                continue

            for sub_state_enum in state_enum.value.sub_states:
                sub_state_enum.value.parent = state_enum
                # print(f'state: {state_enum}, substate:{sub_state_enum}, parent:{sub_state_enum.value.parent}')
                self._states[sub_state_enum] = self._create_state(state, sub_state_enum)

        self._add_transitions()
        self._connect_machine_finished()
        self._machine.start()

    def __getitem__(self, item: Union[QState, QFinalState, Enum]):
        if isinstance(QState, QFinalState):
            return self._states.reverse_search(item)
        else:
            return self._states[item]

    @property
    def current_state(self) -> QState:
        return self._current_state

    @property
    def previous_state(self) -> QState:
        return self._previous_state

    @property
    def current_state_enum(self) -> Enum:
        return self._states.reverse_search(self._current_state)

    @property
    def previous_state_enum(self) -> Enum:
        return self._states.reverse_search(self._previous_state)

    @property
    def current_super_state(self) -> Enum:
        state_enum: Enum = self._states.reverse_search(self._current_state)
        state_desc: StateDescriptor = state_enum.value
        return state_desc.parent

    @property
    def previous_super_state(self) -> Enum:
        state_enum: Enum = self._states.reverse_search(self._previous_state)
        state_desc: StateDescriptor = state_enum.value
        return state_desc.parent

    # endregion

    # region Protected:
    _parents = None  # Parent object
    _states_enum: Enum
    _current_state: Optional[QState] = None
    _previous_state: Optional[QState] = None

    def _create_state(self, machine: Union[QStateMachine, QState, QFinalState], state_enum: Enum) -> QState:
        parent_state = None
        state_desc: StateDescriptor = state_enum.value
        if type(machine) is not QStateMachine:
            # creating a sub-state
            parent_state = machine

        state = QState(parent=parent_state)
        if state_desc.final:
            state = QFinalState(parent=parent_state)

        state.entered.connect(partial(self._update_link_attrs, state))
        self._connect_events_to_parent(state, state_enum)
        if type(machine) is QStateMachine:
            machine.addState(state)

        if state_desc.initial:
            machine.setInitialState(state)
        return state

    def _update_link_attrs(self, state: QState) -> None:
        if self._current_state is None:
            self._current_state = state
        else:
            self._previous_state = self._current_state
            self._current_state = state

        # print(self.previous_state_enum, self.current_state_enum)

    def _connect_machine_finished(self) -> None:
        if self._parents is None:
            return

        for parent in self._parents:
            if hasattr(parent, 'machine_finished'):
                self._machine.finished.connect(parent.machine_finished)

    def _connect_events_to_parent(self, state: QState, state_enum: Enum) -> None:
        if self._parents is None:
            return

        state_entered = self._format_state_substate(state_enum, suffix='entered')
        state_finished = self._format_state_substate(state_enum, suffix='finished')
        state_exited = self._format_state_substate(state_enum, suffix='exited')

        if hasattr(self, state_entered):
            state.entered.connect(getattr(self, state_entered))
        if hasattr(self, state_finished):
            state.entered.connect(getattr(self, state_finished))
        if hasattr(self, state_exited):
            state.entered.connect(getattr(self, state_exited))

        for parent in self._parents:
            if hasattr(parent, state_entered):
                state.entered.connect(getattr(parent, state_entered))
            if hasattr(parent, state_finished):
                state.entered.connect(getattr(parent, state_finished))
            if hasattr(parent, state_exited):
                state.entered.connect(getattr(parent, state_exited))

            if hasattr(parent, 'state_entered'):
                state.entered.connect(partial(parent.state_entered, state, state_enum))

            if hasattr(parent, 'state_finished') and type(state) is not QFinalState:
                state.finished.connect(partial(parent.state_finished, state, state_enum))

            if hasattr(parent, 'state_exited') and type(state) is not QFinalState:
                state.exited.connect(partial(parent.state_exited, state, state_enum))

    def _add_transitions(self) -> None:
        for state_enum, state_qt in self._states.items():
            state_transitions: TransitionsDescriptor = state_enum.value.transitions
            if state_transitions is None:
                continue

            # print(f"From: {state_enum} to {state_transitions.next_state} : {self._target_state_name_to_enum(state_enum, state_transitions.next_state)}")

            target_state = self._states[self._target_state_name_to_enum(state_enum, state_transitions.next_state)]
            # Add signal `to_next` to state

            # Add signal `to_previous` to `target_state` of state
            if type(target_state) is not QFinalState:
                target_state.addTransition(self.to_previous, state_qt)

            if type(state_qt) is not QFinalState:
                state_qt.addTransition(self.to_next, target_state)

                for target_state_name in state_enum.value.transitions.optional:
                    if not hasattr(self, self._signal_format(target_state_name)):
                        raise AttributeError(
                            f"class {self.__class__.__name__} does not have signal attribute "
                            f"`{self._signal_format(target_state_name)}`, define the `signal` as a static attribute"
                        )
                    signal: Signal = getattr(self, self._signal_format(target_state_name))
                    state_qt.addTransition(
                        signal,
                        self._states[self._target_state_name_to_enum(state_enum, target_state_name)]
                    )

    def _target_state_name_to_enum(self, state_enum: Enum, target_name: str) -> Enum:
        state_desc: StateDescriptor = state_enum.value
        if state_desc.parent:
            parent_state: StateDescriptor = state_desc.parent.value
            # print(f'[target name to state enum] substate:{state_enum}, '
            #       f'parent:{state_enum.value.parent}, '
            #       f'return: {parent_state.sub_states[target_name]}')
            return parent_state.sub_states[target_name]
        else:
            return self._states_enum[target_name]

    @staticmethod
    def _signal_format(state_name: str) -> str:
        return f'to_{state_name.lower()}'

    @staticmethod
    def _format_state_substate(state_enum, prefix: Optional[str] = None, suffix: Optional[str] = None) -> str:
        fmt = ''
        if prefix:
            fmt += f'{prefix}_'
        state_desc: StateDescriptor = state_enum.value
        if state_desc.parent:
            fmt = f'state_{state_desc.parent.name.lower()}__{state_enum.name.lower()}'
        else:
            fmt = f'state_{state_enum.name.lower()}'

        if suffix:
            fmt += f'_{suffix}'
        return fmt

    # endregion

    # region Private:
    __default_states_enum = StandardStates
    # endregion
