# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import abc
import enum
import logging

# Library Imports
# […]

# Project Imports
# […]

_logger = logging.getLogger(__name__)


class Condition(abc.ABC):

    class Type(enum.IntEnum):
        TEMPERATURE = enum.auto()
        TIME_OF_DAY = enum.auto()

        def to_class(self) -> Type[Condition]:
            """Convert type into condition class."""
            from sharly.model.condition.temperature import TemperatureCondition
            from sharly.model.condition.time_of_day import TimeOfDayCondition

            if self is Condition.Type.TEMPERATURE:
                return TemperatureCondition
            elif self is Condition.Type.TIME_OF_DAY:
                return TimeOfDayCondition
            else:
                raise NotImplementedError

    def __init__(self) -> None:
        self._associated_item = None

    def __repr__(self) -> str:
        if self.associated_item:
            return f'{self.type.name}({self.value.name})@{self.associated_item}'
        else:
            return f'{self.type.name}({self.value.name})'

    def __hash__(self) -> int:
        return hash((self.type, self.value, self.associated_item))

    def __eq__(self, other: Condition) -> bool:
        return self.type == other.type and self.value == other.value and self.associated_item == other.associated_item

    @property
    def associated_item(self) -> Optional[str]:
        return self._associated_item

    @associated_item.setter
    def associated_item(self, item_name: str) -> None:
        self._associated_item = item_name

    @property
    @abc.abstractmethod
    def type(self) -> Condition.Type:
        pass

    @property
    @abc.abstractmethod
    def value(self) -> enum.IntEnum:
        pass

    @classmethod
    @abc.abstractmethod
    def from_value(cls, real_value: Any) -> Condition:
        """Convert a real value (like temperature etc.) into discrete condition."""
        pass

    @classmethod
    @abc.abstractmethod
    def from_state(cls, state_value: str) -> Condition:
        """Convert an item state into discrete condition."""
        pass

    @classmethod
    @abc.abstractmethod
    def from_enum(cls, enum_value: int) -> Condition:
        """Convert an enum integer (usually from database) into discrete condition."""
        pass
