# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from sharly.model.condition import Condition
    from sharly.model.event import Event
    from sharly.model.event_sequence import EventSequence

# Builtin Imports
import abc
import logging

# Library Imports
# […]

# Project Imports
# […]


_logger = logging.getLogger(__name__)


class Database(abc.ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._connection = self.connect(*args, **kwargs)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'

    @property
    @abc.abstractmethod
    def connection(self) -> Any:
        return self._connection

    @abc.abstractmethod
    def connect(self, *args: Any, **kwargs: Any) -> Any:
        """Connect to the database.

        Returns
        -------
        The database connection.
        """

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the database."""

    @abc.abstractmethod
    def store_conditions(self, conditions: FrozenSet[Condition]) -> int:
        """Store a set of conditions into the database.

        Parameters
        ----------
        conditions
            The set of conditions to store.

        Returns
        -------
        The id of the conditions (if exists).
        """

    @abc.abstractmethod
    def get_conditions_id(self, conditions: FrozenSet[Condition]) -> int:
        """Get the id for a set of conditions.

        Parameters
        ----------
        conditions
            The set of conditions to get the id from.

        Returns
        -------
        The id of the conditions (if exists).

        Raises
        ------
        ValueError, if the set of conditions does not exists yet.
        """

    @abc.abstractmethod
    def get_conditions(self, conditions_id: int) -> FrozenSet[Condition]:
        """Get the conditions for an id.

        Parameters
        ----------
        conditions_id
            The id of the conditions.

        Returns
        -------
        Set of conditions.
        """

    @abc.abstractmethod
    def store_event(self, event: Event) -> None:
        """Store an event into the database.

        Parameters
        ----------
        event
            The event to store into the database.
        """

    @abc.abstractmethod
    def get_events(self, group: Optional[str] = None, interval: Optional[int] = None) -> List[Event]:
        """Get all events from the last interval days for a specific group.

        Parameters
        ----------
        group
            Get only events of a specific group.
        interval
            Get only events of the last interval days (default is all).

        Returns
        -------
        List of matching events.
        """

    @abc.abstractmethod
    def store_event_sequence(self, event_sequence: EventSequence, group: str) -> None:
        """Store an event sequence into the database.

        Parameters
        ----------
        event_sequence
            The event sequence to store.
        group
            The corresponding group.
        """

    @abc.abstractmethod
    def store_event_delay(self, group: str, value: int) -> None:
        """Store the event delay for a given group.

        Parameters
        ----------
        group
            The group associated to the event delay.
        value
            The event delay.
        """

    @abc.abstractmethod
    def get_event_delay(self, group: str) -> int:
        """Get the event delay for a given group.

        Parameters
        ----------
        group
            The associated group.
        """
    @abc.abstractmethod
    def get_event_sequences(self, group: str) -> Dict[FrozenSet[Condition], List[EventSequence]]:
        """Get all event sequences for a specific group.

        Parameters
        ----------
        group
            The associated group.
        """

    @abc.abstractmethod
    def clear_learned(self, database_name: str) -> None:
        """Clear all learned data.

        Parameters
        ----------
        database_name
            The name of the database.
        """
