# TODO: ADD DOCSTRING
from aiogram.fsm.state import State, StatesGroup


class AddTaskStates(StatesGroup):
    """
    AddTaskStates is a class that defines the states for adding a task in a state machine.

    Attributes:
        awaiting_name (State): The state where the system is waiting for the user to provide the task name.
        awaiting_tags (State): The state where the system is waiting for the user to provide the task tags.
    """

    awaiting_name = State()
    awaiting_tags = State()
