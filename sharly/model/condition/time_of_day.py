# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import enum
import datetime
import logging

# Library Imports
# […]

# Project Imports
from sharly.model.condition import Condition

_logger = logging.getLogger(__name__)


class TimeOfDayCondition(Condition):
    class TimeOfDay(enum.IntEnum):
        MORNING = enum.auto()    # 7:00:00 to 10:59:59
        FORENOON = enum.auto()   # 11:00:00 to 12:59:59
        NOON = enum.auto()       # 13:00:00 to 14:59:59
        AFTERNOON = enum.auto()  # 15:00:00 to 17:59:59
        EVENING = enum.auto()    # 18:00:00 to 20:59:59
        NIGHT = enum.auto()      # 21:00:00 to 6:59:59

    def __init__(self, value: TimeOfDay) -> None:
        super().__init__()
        self._value = value

    @property
    def type(self) -> Condition.Type:
        return Condition.Type.TIME_OF_DAY

    @property
    def value(self) -> TimeOfDay:
        return self._value

    @classmethod
    def from_value(cls, real_value: datetime.time) -> TimeOfDayCondition:
        if datetime.time(hour=7) <= real_value < datetime.time(hour=11):
            return cls(cls.TimeOfDay.MORNING)
        elif datetime.time(hour=11) <= real_value < datetime.time(hour=13):
            return cls(cls.TimeOfDay.FORENOON)
        elif datetime.time(hour=13) <= real_value < datetime.time(hour=15):
            return cls(cls.TimeOfDay.NOON)
        elif datetime.time(hour=15) <= real_value < datetime.time(hour=18):
            return cls(cls.TimeOfDay.AFTERNOON)
        elif datetime.time(hour=18) <= real_value < datetime.time(hour=21):
            return cls(cls.TimeOfDay.EVENING)
        else:
            return cls(cls.TimeOfDay.NIGHT)

    @classmethod
    def from_state(cls, state_value: str) -> TimeOfDayCondition:
        raise NotImplementedError

    @classmethod
    def from_enum(cls, enum_value: int) -> TimeOfDayCondition:
        return cls(cls.TimeOfDay(enum_value))
