# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import datetime
import logging
import os
import sqlite3

# Library Imports
# […]

# Project Imports
from sharly.database import Database
from sharly.model.condition import Condition
from sharly.model.event import Event, Item
from sharly.model.event_sequence import EventSequence
from sharly.util.item_list import ITEM_LIST

_logger = logging.getLogger(__name__)


class SQLiteDatabase(Database):
    def __init__(self, database_name: str, clear: bool, **_kwargs: Any) -> None:
        if clear:
            self.__clear(database_name)
        super().__init__(database_name=database_name)
        self.__create_tables(database_name)

    def __clear(self, database_name: str) -> None:
        try:
            os.remove(f'{database_name}.db')
        except FileNotFoundError:
            pass
        except OSError:
            _logger.exception(f'Failed clearing "{database_name}"!')
            raise
        _logger.info(f'Cleared {self}.')

    def __create_tables(self, database_name: str) -> None:
        tables = {
            'conditions': (
                'CREATE TABLE IF NOT EXISTS `conditions` ('
                '   `conditions_id` INTEGER NOT NULL,'
                '   PRIMARY KEY (`conditions_id`)'
                ')'
            ),
            'condition_data': (
                'CREATE TABLE IF NOT EXISTS `condition_data` ('
                '   `conditions_id` INTEGER NOT NULL,'
                '   `condition_type` INTEGER NOT NULL,'
                '   `condition_value` INTEGER NOT NULL,'
                '   `item_name` TEXT NOT NULL,'
                '   PRIMARY KEY (`conditions_id`, `condition_type`, `item_name`)'
                ')'
            ),
            'events': (
                'CREATE TABLE IF NOT EXISTS `events` ('
                '   `event_id` INTEGER NOT NULL,'
                '   `item_name` TEXT NOT NULL,'
                '   `old_state` TEXT NOT NULL,'
                '   `new_state` TEXT NOT NULL,'
                '   `timestamp` TIMESTAMP NOT NULL,'
                '   `conditions_id` INT NOT NULL,'
                '   PRIMARY KEY (`event_id`),'
                '   FOREIGN KEY (`conditions_id`) REFERENCES conditions(`conditions_id`)'
                ')'
            ),
            'event_sequences': (
                'CREATE TABLE IF NOT EXISTS `event_sequences` ('
                '   `event_sequence_id` INTEGER NOT NULL,'
                '   `group` TEXT NOT NULL,'
                '   PRIMARY KEY (`event_sequence_id`)'
                ')'
            ),
            'event_sequence_data': (
                'CREATE TABLE IF NOT EXISTS `event_sequence_data` ('
                '   `event_sequence_id` INTEGER NOT NULL,'
                '   `event_u_id` INTEGER NOT NULL,'
                '   `event_u_occurrence` INTEGER NOT NULL,'
                '   `event_v_id` INTEGER NOT NULL,'
                '   `event_v_occurrence` INTEGER NOT NULL,'
                '   `weight` INTEGER NOT NULL,'
                '   PRIMARY KEY (`event_sequence_id`, `event_u_id`, `event_v_id`)'
                ')'
            ),
            'event_delays': (
                'CREATE TABLE IF NOT EXISTS `event_delays` ('
                '   `group` TEXT NOT NULL,'
                '   `value` INTEGER NOT NULL,'
                '   PRIMARY KEY (`group`)'
                ')'
            )
        }
        cursor = self.connection.cursor()
        for table_name, query in tables.items():
            try:
                cursor.execute(query)
            except sqlite3.Error:
                _logger.exception(f'Failed creating table "{table_name}" for database "{database_name}" on {self}.')
                cursor.close()
                raise
        cursor.close()

    @property
    def connection(self) -> sqlite3.Connection:
        return super().connection

    def connect(self, database_name: str) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(f'{database_name}.db', detect_types=sqlite3.PARSE_DECLTYPES,  # parse timestamp
                                         isolation_level=None)  # autocommit = True
        except sqlite3.Error:
            _logger.exception(f'Failed connecting to {self}!')
            raise

        _logger.info(f'Connected to {self}.')
        return connection

    def disconnect(self) -> None:
        self.connection.close()

    def store_conditions(self, conditions: FrozenSet[Condition]) -> int:
        cursor = self.connection.cursor()
        query = 'INSERT INTO `conditions` (`conditions_id`) VALUES (NULL)'
        try:
            cursor.execute(query)
        except sqlite3.Error:
            _logger.exception(f'Failed storing new conditions into {self}: {conditions}!')
            return -1

        conditions_id = cursor.lastrowid
        query = 'INSERT INTO `condition_data` ' \
                '(`conditions_id`, `condition_type`, `condition_value`, `item_name`) VALUES ' \
                '(?, ?, ?, ?)'
        data = [(conditions_id, int(c.type), int(c.value), c.associated_item or 'NULL') for c in conditions]
        try:
            cursor.executemany(query, data)
        except sqlite3.Error:
            _logger.exception(f'Failed storing new conditions into {self}: {conditions}!')
            return -1

        cursor.close()
        return conditions_id

    def get_conditions_id(self, conditions: FrozenSet[Condition]) -> int:
        cursor = self.connection.cursor()
        query = 'SELECT `conditions_id`, `condition_type`, `condition_value`, `item_name` FROM condition_data'
        try:
            cursor.execute(query)
        except sqlite3.Error:
            _logger.exception(f'Could not get conditions from {self} for conditions: {conditions}!')
            raise ValueError

        stored_conditions_dict = {}
        for conditions_id, condition_type, condition_value, item_name in cursor:
            if conditions_id not in stored_conditions_dict:
                stored_conditions_dict[conditions_id] = set()

            condition = Condition.Type(condition_type).to_class().from_enum(condition_value)
            if item_name != 'NULL':
                condition.associated_item = item_name
            stored_conditions_dict[conditions_id].add(condition)
        cursor.close()

        for conditions_id, stored_conditions in stored_conditions_dict.items():
            if stored_conditions == conditions:
                return conditions_id
        raise ValueError

    def get_conditions(self, conditions_id: int) -> FrozenSet[Condition]:
        cursor = self.connection.cursor()
        query = 'SELECT `conditions_id`, `condition_type`, `condition_value`, `item_name` FROM condition_data ' \
                'WHERE `conditions_id` = ?'
        data = (conditions_id,)
        try:
            cursor.execute(query, data)
        except sqlite3.Error:
            _logger.exception(f'Could not get conditions from {self} for conditions_id={conditions_id}!')
            cursor.close()
            return frozenset()

        conditions = set()
        for _, condition_type, condition_value, item_name in cursor:
            condition = Condition.Type(condition_type).to_class().from_enum(condition_value)
            if item_name != 'NULL':
                condition.associated_item = item_name
            conditions.add(condition)
        cursor.close()
        return frozenset(conditions)

    def store_event(self, event: Event) -> None:
        try:
            conditions_id = self.get_conditions_id(event.conditions)
        except ValueError:
            conditions_id = self.store_conditions(event.conditions)
            if conditions_id == -1:  # something went wrong
                _logger.exception(f'Failed storing event into {self}: {event}!')
                return

        cursor = self.connection.cursor()
        query = 'INSERT INTO events ' \
                '(`event_id`, `item_name`, `old_state`, `new_state`, `timestamp`, `conditions_id`) VALUES ' \
                '(NULL, ?, ?, ?, ?, ?)'
        data = (event.item.name, event.item.old_state, event.item.new_state, event.timestamp, conditions_id)
        try:
            cursor.execute(query, data)
        except sqlite3.Error:
            _logger.exception(f'Failed storing event into {self}: {event}!')
        cursor.close()

    def get_events(self, group: Optional[str] = None, interval: Optional[int] = None) -> List[Event]:
        cursor = self.connection.cursor()
        if not interval:
            query = 'SELECT `event_id`, `item_name`, `old_state`, `new_state`, `timestamp`, `conditions_id` ' \
                    'FROM events'
            data = None
        else:
            query = 'SELECT `event_id`, `item_name`, `old_state`, `new_state`, `timestamp`, `conditions_id` ' \
                    'FROM events WHERE `timestamp` BETWEEN ? AND ? ORDER BY `event_id`'
            data = (datetime.datetime.now() - datetime.timedelta(days=interval), datetime.datetime.now())

        try:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)
        except sqlite3.Error:
            _logger.exception(f'Could not get events from {self} for group "{group}" and interval={interval}!')
            cursor.close()
            return []

        events = []
        for event_id, item_name, old_state, new_state, timestamp, conditions_id in cursor.fetchall():
            if not ITEM_LIST.is_valid(item_name, old_state, new_state, group):
                continue

            conditions = self.get_conditions(conditions_id)
            item = Item(item_name, old_state, new_state)
            event = Event(item, timestamp, conditions, event_id)
            events.append(event)
        cursor.close()
        return events

    def store_event_sequence(self, event_sequence: EventSequence, group: str) -> None:
        if len(event_sequence) < 2:  # do not store useless event sequences
            _logger.debug(f'Skipped storing useless event sequence (node-count={event_sequence.number_of_nodes()}).')
            return

        cursor = self.connection.cursor()
        query = 'INSERT INTO `event_sequences` (`event_sequence_id`, `group`) VALUES (NULL, ?)'
        data = (group,)
        try:
            cursor.execute(query, data)
        except sqlite3.Error:
            _logger.exception(f'Failed storing new event sequence into {self} for group "{group}"!')
            cursor.close()
            return

        event_sequence_id = cursor.lastrowid
        query = 'INSERT INTO `event_sequence_data` ' \
                '(`event_sequence_id`, `event_u_id`, `event_u_occurrence`, ' \
                '`event_v_id`, `event_v_occurrence`, `weight`) VALUES (?, ?, ?, ?, ?, ?)'

        data = []
        for event_u, event_v, d in event_sequence.edges(data=True):
            if d['weight'] == 0:  # do not store zero edges
                continue

            event_u_o = event_sequence.nodes[event_u]['occurrence']
            event_v_o = event_sequence.nodes[event_v]['occurrence']
            data.append((event_sequence_id, event_u.id, event_u_o, event_v.id, event_v_o, d['weight']))

        try:
            cursor.executemany(query, data)
        except sqlite3.Error:
            _logger.exception(f'Failed storing new event sequence into {self} for group "{group}"!')

        cursor.close()

    def store_event_delay(self, group: str, value: int) -> None:
        cursor = self.connection.cursor()
        query = 'INSERT OR REPLACE INTO `event_delays` (`group`, `value`) VALUES (?, ?)'
        data = (group, value)
        try:
            cursor.execute(query, data)
        except sqlite3.Error:
            _logger.exception(f'Failed storing event delay={value} for group "{group}"!')
        cursor.close()

    def get_event_delay(self, group: str) -> int:
        cursor = self.connection.cursor()
        query = 'SELECT `value` FROM `event_delays` WHERE `group` = ?'
        data = (group,)
        try:
            cursor.execute(query, data)
        except sqlite3.Error:
            _logger.exception(f'Failed getting event delay for group "{group}"!')
            cursor.close()
            return 0

        event_delay = cursor.fetchone()[0]
        cursor.close()
        return event_delay

    def get_event_sequences(self, group: str) -> Dict[FrozenSet[Condition], List[EventSequence]]:
        events = {event.id: event for event in self.get_events(group)}
        cursor = self.connection.cursor()
        query = 'SELECT `event_sequence_id` FROM `event_sequences` WHERE `group` = ?'
        data = (group,)

        try:
            cursor.execute(query, data)
        except sqlite3.Error:
            _logger.exception(f'Failed getting stored event sequences for group "{group}"!')
            cursor.close()
            return {}

        event_sequences = {}
        for event_sequence_id, in cursor.fetchall():
            query = 'SELECT `event_u_id`, `event_u_occurrence`, `event_v_id`, `event_v_occurrence`, ' \
                    '`weight` FROM `event_sequence_data` WHERE `event_sequence_id` = ?'
            data = (event_sequence_id,)

            try:
                cursor.execute(query, data)
            except sqlite3.Error:
                _logger.exception(f'Failed getting event sequence ({event_sequence_id}) data for group "{group}"!')
                continue

            event_sequence = EventSequence(event_sequence_id)
            try:
                for eu_id, euo, ev_id, evo, w in cursor.fetchall():
                    event_u = events[eu_id]
                    event_v = events[ev_id]

                    event_sequence.add_node(event_u, occurrence=euo)
                    event_sequence.add_node(event_v, occurrence=evo)
                    event_sequence.add_edge(event_u, event_v, weight=w)
            except KeyError:
                _logger.exception(f'Invalid event sequence! Some events where not found but declared! - Skipping')
                continue

            if event_sequence.conditions not in event_sequences:
                event_sequences[event_sequence.conditions] = []

            event_sequences[event_sequence.conditions].append(event_sequence)
        cursor.close()
        return event_sequences

    def clear_learned(self, database_name: str) -> None:
        tables = ('event_sequences', 'event_sequence_data', 'event_delays')
        cursor = self.connection.cursor()
        for table_name in tables:
            query = f'DROP TABLE IF EXISTS {table_name}'
            try:
                cursor.execute(query)
            except sqlite3.Error:
                _logger.exception(f'Failed clearing table {table_name}!')
        cursor.close()
        self.__create_tables(database_name)
