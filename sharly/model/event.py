# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from sharly.model.condition import Condition

# Builtin Imports
import dataclasses
import datetime
import logging

# Library Imports
# […]

# Project Imports
# […]

_logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Item:
    name: str
    old_state: str
    new_state: str


@dataclasses.dataclass(frozen=True)
class Event:
    item: Item
    timestamp: datetime.datetime = dataclasses.field(compare=False)
    conditions: FrozenSet[Condition] = dataclasses.field(default_factory=frozenset, compare=False)

    # Database variables
    id: int = dataclasses.field(default=0, compare=False)

    def __repr__(self) -> str:
        return f'{self.item.name}({self.item.old_state}=>{self.item.new_state}) [{self.timestamp}]'
