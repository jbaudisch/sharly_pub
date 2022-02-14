# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import enum
import logging

# Library Imports
# […]

# Project Imports
from sharly.model.condition import Condition

_logger = logging.getLogger(__name__)


class TemperatureCondition(Condition):
    class Temperature(enum.IntEnum):
        VERY_COLD = enum.auto()     # <-15°C
        COLD = enum.auto()          # -15°C to -10°C
        VERY_COOL = enum.auto()     # -10°C to -5°C
        COOL = enum.auto()          # -5°C to 0°C
        COMFORTABLE = enum.auto()   # 0°C to 15°C
        WARM = enum.auto()          # 15°C to 20°C
        VERY_WARM = enum.auto()     # 20°C to 25°C
        HOT = enum.auto()           # 25°C to 30°C
        VERY_HOT = enum.auto()      # >30°C

    def __init__(self, value: Temperature) -> None:
        super().__init__()
        self._value = value

    @property
    def type(self) -> Condition.Type:
        return Condition.Type.TEMPERATURE

    @property
    def value(self) -> Temperature:
        return self._value

    @classmethod
    def from_value(cls, real_value: float) -> TemperatureCondition:
        if real_value < -15:
            return cls(cls.Temperature.VERY_COLD)
        elif -15 <= real_value < -10:
            return cls(cls.Temperature.COLD)
        elif -10 <= real_value < -5:
            return cls(cls.Temperature.VERY_COOL)
        elif -5 <= real_value < 0:
            return cls(cls.Temperature.COOL)
        elif 0 <= real_value <= 15:
            return cls(cls.Temperature.COMFORTABLE)
        elif 15 < real_value <= 20:
            return cls(cls.Temperature.WARM)
        elif 20 < real_value <= 25:
            return cls(cls.Temperature.VERY_WARM)
        elif 25 < real_value <= 30:
            return cls(cls.Temperature.HOT)
        else:
            return cls(cls.Temperature.VERY_HOT)

    @classmethod
    def from_state(cls, state_value: str) -> TemperatureCondition:
        return cls.from_value(float(state_value))

    @classmethod
    def from_enum(cls, enum_value: int) -> TemperatureCondition:
        return cls(cls.Temperature(enum_value))
