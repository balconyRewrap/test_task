"""
This module defines state groups for handling tasks in a state machine using aiogram.

Classes:
    AddTaskStates (StatesGroup): Defines states for adding a task.

    SearchStates (StatesGroup): Defines states for searching tasks.

"""
from aiogram.fsm.state import State, StatesGroup


class AddTaskStates(StatesGroup):
    """
    AddTaskStates is a class that defines the states for adding a task in a state machine.

    Attributes:
        waiting_name (State): The state where the system is waiting for the user to provide the task name.
        waiting_tags (State): The state where the system is waiting for the user to provide the task tags.
    """

    waiting_name = State()
    waiting_tags = State()


class SearchStates(StatesGroup):
    """
    SearchStates is a class that defines different states for a search task.

    Attributes:
        waiting_for_query (State): State indicating that the system is waiting for a search query from the user.
        waiting_for_tags (State): State indicating that the system is waiting for tags related to the search query.
        listing_tasks (State): State indicating that the system is listing tasks based on the search query and tags.
    """

    waiting_for_query = State()
    waiting_for_tags = State()
    listing_tasks = State()
