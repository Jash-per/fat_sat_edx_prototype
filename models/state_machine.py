# model.py
from enum import Enum
from abc import ABC, abstractmethod
from functools import partial
from dataclasses import dataclass, field
from typing import Optional, Union, List, Any, Tuple
from PySide6.QtCore import QObject, Signal
from PySide6.QtStateMachine import (QStateMachine, QState, QFinalState, QSignalTransition)
from util.functions import SearchDict


@dataclass(frozen=True)
class TransitionsDescriptor:
    next_state: Union[str, tuple, None]
    prev_state: Optional[str] = None
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
    IDLE = StateDescriptor('IDLE', TransitionsDescriptor('STARTING', optional=['STOPPING', 'ERROR'], prev_state='IDLE'), initial=True)
    STARTING = StateDescriptor('STARTING', TransitionsDescriptor('EXECUTE', optional=['STOPPING', 'ERROR']))
    EXECUTE = StateDescriptor('EXECUTE', TransitionsDescriptor('COMPLETE', optional=['STOPPING', 'ERROR']))
    COMPLETE = StateDescriptor('COMPLETE', final=False)
    # Controls don't allow previous transitions...
    STOPPING = StateDescriptor('STOPPING', TransitionsDescriptor('STOPPED', optional=['ERROR'], prev_state='STOPPING'))
    STOPPED = StateDescriptor('STOPPED', TransitionsDescriptor('IDLE', optional=['ERROR']))
    ABORTING = StateDescriptor('ABORTING', TransitionsDescriptor('ABORTED', optional=['ERROR'], prev_state='ABORTING'))
    ABORTED = StateDescriptor('ABORTED', TransitionsDescriptor('RESETTING', optional=['ERROR']))
    RESETTING = StateDescriptor('RESETTING', TransitionsDescriptor('IDLE', optional=['ERROR'], prev_state='RESETTING'))
    ERROR = StateDescriptor('ERROR', TransitionsDescriptor('RESETTING', optional=['ERROR'], prev_state='IDLE'))


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


class OptionTransition(QSignalTransition):

    def __init__(self, option: Tuple[int, str, Enum], signal: Signal):
        super(OptionTransition, self).__init__(signal)
        self.option = option

    def eventTest(self, e):
        if not super().eventTest(e):
            return False
        return e.arguments()[0] in self.option


class StateMachineModel(QObject):
    """
    Class representing a state machine. It includes multiple states, signals for handling different
    state transitions, helper methods for creating and managing states.
    """

    # region Public:
    to_previous = Signal()
    to_next = Signal()
    to_option = Signal(tuple)
    to_error = Signal()
    to_stopping = Signal()
    skip = Signal()

    def __init__(self, parents: Union[Any, List, None] = None, states_enum: Optional[Enum] = None) -> None:
        """
        Initializes StateMachineModel.

        :param parents: Parent states of the state machine (optional).
        :param states_enum: An Enum of states (optional).
        """
        #
        super().__init__()
        if parents is not None and not isinstance(parents, list):
            self._parents = [parents]
        else:
            self._parents = parents

        for parent in self._parents:
            parent.statemachine = self

        if states_enum is None:
            self._states_enum = self.__default_states_enum
        else:
            self._states_enum = states_enum

        self._machine = QStateMachine()
        self._states = SearchDict()

        for state_enum in self._states_enum:
            self._create_and_assign_state(self._machine, state_enum)

        self._add_transitions()
        self._connect_machine_finished()
        self._machine.start()

    def __getitem__(self, item: Union[QState, QFinalState, Enum]):
        """
        Retrieves a state from the state machine.

        :param item: The state identifier, either a QState/QFinalState instance or an enumeration.
        :return: The corresponding state from the state machine.
        """
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

    @property
    def current_state_tree(self) -> List[Enum]:
        tree = []
        state_enum: Enum = self._states.reverse_search(self._current_state)
        tree.append(state_enum)
        n = 0
        while (n < 100):
            state_desc: StateDescriptor = state_enum.value
            if state_desc.parent:
                state_enum = state_desc.parent
                tree.append(state_enum)
            else:
                break
            n += 1
        tree.reverse()
        return tree

    def goto(self, state: Union[QState, Enum]):
        """
        This function stops the current state machine, sets a new initial state, and starts the machine again.

        :param state: The state to which the machine will transition. This can be an instance of a QState or an Enum.
        :type state: Union[QState, Enum]

        :raises KeyError: If the provided state does not exist in the state machine.

        :return: None
        """
        state = self[state]
        self.machine.stop()
        self.setInitialState(state)
        self.start()

    # endregion

    # region Protected:
    _parents = None  # Parent object
    _stateful_view = None
    _states_enum: Enum
    _current_state: Optional[QState] = None
    _previous_state: Optional[QState] = None

    def _create_and_assign_state(self, parent, state_enum):
        state = self._states[state_enum] = self._create_state(parent, state_enum)
        if not state_enum.value.sub_states:
            return
        for sub_state_enum in state_enum.value.sub_states:
            sub_state_enum.value.parent = state_enum
            self._create_and_assign_state(state, sub_state_enum)

    def _create_state(self, machine: Union[QStateMachine, QState, QFinalState], state_enum: Enum) -> QState:
        """
        Creates a new state in the state machine.

        :param machine: An instance of QStateMachine, QState or QFinalState.
        :param state_enum: An Enum that describes the state.
        :return: A QState instance representing the created state.
        """
        parent_state = None
        state_desc: StateDescriptor = state_enum.value
        if not isinstance(machine, QStateMachine):
            # creating a sub-state
            parent_state = machine

        state = QState(parent=parent_state)
        if state_desc.final:
            state = QFinalState(parent=parent_state)

        state.entered.connect(partial(self._update_link_attrs, state))
        self._connect_events_to_parents(state, state_enum)
        if isinstance(machine, QStateMachine):
            machine.addState(state)

        if state_desc.initial:
            machine.setInitialState(state)
        return state

    def _update_link_attrs(self, state: QState) -> None:
        """
        Updates link attributes.

        :param state: An instance of QState.
        """
        if self._current_state is None:
            self._current_state = state
        else:
            self._previous_state = self._current_state
            self._current_state = state

        # print(self.previous_state_enum, self.current_state_enum)

    def _connect_machine_finished(self) -> None:
        """
        Connects the machine_finished method of parent with the machine's finished signal.
        """
        if self._parents is None:
            return

        for parent in self._parents:
            if hasattr(parent, 'machine_finished'):
                self._machine.finished.connect(parent.machine_finished)

    def _connect_events_to_parents(self, state: QState, state_enum: Enum) -> None:
        """
        Connects state events to parent.

        :param state: An instance of QState.
        :param state_enum: An instance of Enum that represents the state.
        """
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

            if hasattr(parent, 'state_finished') and not isinstance(state, QFinalState):
                state.finished.connect(partial(parent.state_finished, state, state_enum))

            if hasattr(parent, 'state_exited') and not isinstance(state, QFinalState):
                state.exited.connect(partial(parent.state_exited, state, state_enum))

    def _add_transitions(self) -> None:
        """
        Adds transitions to states in the state machine.
        """
        for state_enum, state in self._states.items():
            state_transitions: TransitionsDescriptor = state_enum.value.transitions
            if state_transitions is None:
                continue

            # print(f"From: {state_enum} to {state_transitions.next_state} : {self._target_state_name_to_enum(state_enum, state_transitions.next_state)}")
            if isinstance(state_transitions.next_state, tuple):
                for num, option_state_name in enumerate(state_transitions.next_state):
                    self._add_option_transitions(state, state_enum, num, option_state_name)
                    self._add_prev_transition(state, state_enum, target_state_name=option_state_name)

            else:
                self._add_next_transition(state, state_enum)
                self._add_prev_transition(state, state_enum)

            self._add_optional_transitions(state, state_enum)

    def _add_next_transition(self, state: QState, state_enum: Enum) -> None:
        target_state_name: str = state_enum.value.transitions.next_state
        if not target_state_name:
            return

        target_state_enum: Enum = self._target_state_name_to_enum(state_enum, target_state_name)
        target_state: QState = self._states[target_state_enum]
        if not isinstance(state, QFinalState):
            state.addTransition(self.to_next, target_state)

    def _add_prev_transition(self, state: QState, state_enum: Enum, target_state_name: Optional[str] = None) -> None:
        if target_state_name is None:
            target_state_name: str = state_enum.value.transitions.next_state

        target_state_enum: Enum = self._target_state_name_to_enum(state_enum, target_state_name)
        target_state: QState = self._states[target_state_enum]
        if type(target_state) is QFinalState:
            return

        target_transitions: TransitionsDescriptor = target_state_enum.value.transitions
        if target_transitions is None:
            target_transitions = TransitionsDescriptor(None)

        if target_transitions.prev_state is None:
            target_state.addTransition(self.to_previous, state)
        elif target_transitions.prev_state != state_enum.name and target_transitions.prev_state != target_state_name:
            previous_state_enum = self._target_state_name_to_enum(state_enum, target_transitions.prev_state)
            target_state.addTransition(self.to_previous, self._states[previous_state_enum])
        else:
            # The previous state is equal to the current state: omit previous transition
            pass

    def _add_option_transitions(self, state: QState, state_enum: Enum, num: int, option_state_name: str) -> None:
        option_state_enum = self._target_state_name_to_enum(state_enum, option_state_name)
        option_state = self._states[option_state_enum]
        if not isinstance(state, QFinalState):
            if num == 0:
                state.addTransition(self.to_next, option_state)

            transition = OptionTransition((num, option_state_name, option_state_enum), self.to_option)
            transition.setTargetState(option_state)
            state.addTransition(transition)

    def _add_optional_transitions(self, state: QState, state_enum: Enum) -> None:
        if isinstance(state, QFinalState):
            return
        for target_state_name in state_enum.value.transitions.optional:
            if not hasattr(self, self._signal_format(target_state_name)):
                raise AttributeError(
                    f"class {self.__class__.__name__} does not have signal attribute "
                    f"`{self._signal_format(target_state_name)}`, define the `signal` as a static attribute"
                )
            signal: Signal = getattr(self, self._signal_format(target_state_name))
            state.addTransition(
                signal,
                self._states[self._target_state_name_to_enum(state_enum, target_state_name)]
            )

    def _target_state_name_to_enum(self, state_enum: Enum, target_name: str) -> Enum:
        """
        Converts target state name to Enum.

        :param state_enum: The Enum of the current state.
        :param target_name: The name of the target state.
        :return: The Enum of the target state.
        """
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
        """
        Format the signal name based on the state name.

        :param state_name: The name of the state.
        :return: Formatted signal name.
        """
        return f'to_{state_name.lower()}'

    @staticmethod
    def _format_state_substate(state_enum, prefix: Optional[str] = None, suffix: Optional[str] = None) -> str:
        """
        Format the combination of state and substate.

        :param state_enum: The state Enum.
        :param prefix: The prefix string.
        :param suffix: The suffix string.
        :return: Formatted string of state and substate.
        """
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
