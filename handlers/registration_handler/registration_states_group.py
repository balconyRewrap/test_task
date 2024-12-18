"""
A module that defines the states used in the registration process.

Classes:
    RegistrationStates(StatesGroup): A class used to represent the different states in the registration process.
            awaiting_name (State): Represents the state where the system is waiting for the user to provide their name.
            awaiting_phone (State):
            Represents the state where the system is waiting for the user to provide their phone number.
            registered (State): Represents the state where the user has completed the registration process.

"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """
    A class used to represent the different states in the registration process.

    Attributes:
    awaiting_name : State  # noqa: RST301
        Represents the state where the system is waiting for the user to provide their name.

    awaiting_phone : State
        Represents the state where the system is waiting for the user to provide their phone number.

    registered : State
        Represents the state where the user has completed the registration process.
    """

    awaiting_name = State()
    awaiting_phone = State()
    registered = State()
