# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from sharly.model.event import Event

# Builtin Imports
import logging
import os

# Library Imports
import matplotlib.pyplot as plt

# Project Imports
from sharly.application import Application
from sharly.database.factory import DatabaseFactory
from sharly.model.event_sequence import EventSequence
from sharly.util.config import CONFIG
from sharly.util.item_list import ITEM_LIST

_logger = logging.getLogger(__name__)


class LearnApplication(Application):
    def __init__(self, learning_interval: int) -> None:
        self._learning_interval = learning_interval
        self._database = DatabaseFactory.get_database(
            CONFIG.database_engine,
            username=CONFIG.database_user, password=CONFIG.database_password,
            host=CONFIG.database_host, port=CONFIG.database_port,
            database_name=CONFIG.database_name, clear=False
        )
        self._database.clear_learned(CONFIG.database_name)

    def __calculate_event_delay(self, events: List[Event], frame: Dict[int, int]) -> int:
        """Calculate the time (in sec) allowed to pass between two events, which fits best to represent user behaviour.

        This method tries to find a parameter T, which separates the event sequences
        in the best way. To do so, this method iteratively increases T until
        the found sequences become stable.

        Parameters
        ----------
        events
            List of events to use.
        frame
            Structure to store data points.

        Returns
        -------
        The best event delay in seconds.
        """
        t = CONFIG.t_init
        while True:
            stable, new_t = self.__sequences_stable(events, t, frame)
            if stable:
                break
            t = new_t
        return t

    def __sequences_stable(self, events: List[Event], t: int, frame: Dict[int, int]) -> Tuple[bool, int]:
        """Check if all sequences are stable with given time parameter.

        Sequences are specified as stable if the amount of event-pairs does not
        change more then N for all T'. N is a fixed preset parameter (see config).
        T' is a value which is iterated from T to T + T_inc_stable.

        Parameters
        ----------
        events
            List of events to use.
        t
            Time which is allowed to pass between two events to belong to the same sequence.
        frame
            Structure to store data points.

        Returns
        -------
        True, if sequences are stable, False otherwise plus the new T value.
        """
        _logger.debug(f'-> Checking if sequences are stable with t = {t}:')
        for t_ in range(t, t + CONFIG.t_inc_stable, CONFIG.t_inc):
            number_of_pairs_now = self.__number_of_pairs(events, t_)
            number_of_pairs_future = self.__number_of_pairs(events, t_ + CONFIG.t_inc)
            if t_ not in frame:
                frame[t_] = number_of_pairs_now

            if abs(number_of_pairs_now - number_of_pairs_future) > CONFIG.n:
                _logger.debug(f'   No, found unstable pair-increment at t = {t_}')
                return False, t_ + CONFIG.t_inc

        _logger.debug(f'   Yes, stable')
        return True, 0

    def __number_of_pairs(self, events: List[Event], t: int) -> int:  # List[int]:
        """Calculate the number of pairs of events over all event sequences.

        Parameters
        ----------
        events
            List of events to use.
        t
            Time which is allowed to pass between two events to belong to the same sequence.

        Returns
        -------
        List of number of event-pairs for all sequences.
        """
        number_of_pairs = 0  # []
        for event_sequence in self.__generate_event_sequences(events, t):
            number_of_pairs += event_sequence.size()
        return number_of_pairs

    @staticmethod
    def __generate_event_sequences(events: List[Event], event_delay: int) -> Generator[EventSequence, None, None]:
        """Generate event sequences.

        Parameters
        ----------
        events
            List of events to use.
        event_delay
            Time which is allowed to pass between two events to belong to the same sequence.

        Returns
        -------
        Generated sequences.
        """
        event_sequence = EventSequence()
        previous = events[0]
        event_sequence.add_event(previous, event_delay)

        for event in events[1:]:
            if (event == previous) and ((event.timestamp - previous.timestamp).total_seconds() < CONFIG.t_inc):
                previous = event
                continue

            if not event_sequence.add_event(event, event_delay):
                yield event_sequence.copy()
                event_sequence.clear()
                event_sequence.add_event(event, event_delay)

            previous = event

        yield event_sequence

    def start(self, visualize: bool, visualize_zero_edges: bool, plot: bool) -> None:
        _logger.info(f'Learning started with an interval of {self._learning_interval} days.')
        for group in ITEM_LIST.groups:
            events = self._database.get_events(group, self._learning_interval)
            if not events:
                _logger.info(f'No events found for group "{group}" in the last {self._learning_interval} days - skip.')
                continue

            frame: Dict[int, int] = {}
            event_delay = self.__calculate_event_delay(events, frame)
            if plot:
                if os.path.exists(group + '_data.png'):
                    os.remove(group + '_data.png')
                data = sorted(frame.items())
                x, y = zip(*data)
                plt.plot(x, y, label=group)
                plt.legend()
                plt.savefig(group + '_data.png')
                plt.close()

            self._database.store_event_delay(group, event_delay)
            _logger.info(f'Calculated best event delay for group "{group}": {event_delay}s')

            event_sequences: List[EventSequence] = []
            i = 0
            for event_sequence in self.__generate_event_sequences(events, event_delay):
                for j in range(len(event_sequences)):
                    equal = (event_sequence == event_sequences[j])
                    if equal:
                        event_sequences[j] += event_sequence
                        break
                else:
                    event_sequences.append(event_sequence)

                i += 1

            _logger.info(f'Generated {i} event sequences for group "{group}".')
            _logger.info(f'Merged down to {len(event_sequences)} event sequences for group "{group}".')

            _logger.info(f'Storing event sequences for group "{group}".')
            for i, event_sequence in enumerate(event_sequences):
                self._database.store_event_sequence(event_sequence, group)
                if visualize:
                    event_sequence.visualize(f'{group}/{i}', visualize_zero_edges)

    def stop(self) -> None:
        self._database.disconnect()
