# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import json
import logging

# Library Imports
# […]

# Project Imports
from sharly.model.condition import Condition
from sharly.util.config import CONFIG

_logger = logging.getLogger(__name__)


class _ItemList:

    def __init__(self, filename: str) -> None:
        self._items: Dict[str, Tuple[Set, Set]] = {}
        self._conditions: Dict[str, Condition.Type] = {}
        self._rejected_states: Set[str] = set()
        self.__load(filename)

    def __load(self, filename: str) -> None:
        try:
            with open(filename) as fp:
                data = json.load(fp)

                for item_dict in data.get('items', []):
                    try:
                        name = item_dict['name']
                    except KeyError as e:
                        raise ValueError(f'Missing option {e} on item entry: {item_dict}!')

                    groups = item_dict.get('groups', [])
                    states = item_dict.get('states', [])

                    if type(groups) is str:
                        groups = {groups}
                    elif type(groups) is list:
                        groups = set(groups)
                    else:
                        raise ValueError(f'Invalid groups option for item "{name}"!')

                    if type(states) is str:
                        states = {states}
                    elif type(states) is list:
                        states = set(states)
                    else:
                        raise ValueError(f'Invalid states option for item "{name}"!')

                    self._items[name] = (groups, states)

                for condition_dict in data.get('conditions', []):
                    try:
                        name = condition_dict['name']
                    except KeyError as e:
                        raise ValueError(f'Missing option {e} on condition entry: {condition_dict}!')

                    try:
                        c_type = condition_dict['type']
                    except KeyError as e:
                        raise ValueError(f'Missing option {e} on condition entry: {condition_dict}!')

                    try:
                        c_type = Condition.Type[c_type.upper()]
                    except KeyError as e:
                        raise ValueError(f'Invalid condition type {e}!')

                    self._conditions[name] = c_type

                for state in data.get('rejected_states', []):
                    self._rejected_states.add(state)

        except IOError:
            _logger.exception(f'Could not find item list file: {filename}!')
            raise
        except ValueError:
            _logger.exception(f'Could not parse item list file: {filename}!')
            raise

    @property
    def conditions(self) -> ItemsView[str, Condition.Type]:
        return self._conditions.items()

    @property
    def groups(self) -> Set[str]:
        return set([group for groups, _ in self._items.values() for group in groups])

    def get_item_groups(self, item_name: str) -> Set[str]:
        """Get the groups associated with an item.

        Parameters
        ----------
        item_name : str
            The name of the item the groups should be get.
        """
        try:
            return self._items[item_name][0]
        except KeyError:
            return set()

    def get_item_states(self, item_name: str) -> Set[str]:
        """Get the allowed states associated with an item.

        Parameters
        ----------
        item_name : str
            The name of the item the states should be get.
        """
        try:
            return self._items[item_name][1]
        except KeyError:
            return set()

    def is_valid(self, item_name: str, old_state: str, new_state: str, group: Optional[str] = None) -> bool:
        """Check if an item is valid to use for learning.
        Parameters
        ----------
        item_name : str
            The name of the item.
        old_state : str
            The old state of the item.
        new_state : str
            The new state of the item.
        group : str, optional
            The group which this item must be associated to be accepted.
        """
        if item_name not in self._items:
            return False

        if old_state in self._rejected_states or new_state in self._rejected_states:
            return False

        accepted_groups, accepted_states = self._items[item_name]
        if new_state not in accepted_states:
            return False

        if group is not None:
            if group not in accepted_groups:
                return False

        return True


ITEM_LIST = _ItemList(CONFIG.item_list)
