# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from sharly.model.condition import Condition
    from sharly.model.event_sequence import EventSequence

# Builtin Imports
import logging

# Library Imports
# […]

# Project Imports
from sharly.util.config import CONFIG

_logger = logging.getLogger(__name__)


class ExplanationModule:
    def __init__(self, event_sequences: Dict[str, Dict[FrozenSet[Condition], List[EventSequence]]]) -> None:
        self._event_sequences = event_sequences

    def explain_anomaly(self, anomaly: EventSequence, group: str) -> Tuple[str, Optional[EventSequence]]:
        """Explain an anomaly.

        Parameters
        ----------
        anomaly
            The event sequence anomaly which should be explained.
        group
            The group of the anomaly.

        Returns
        -------
        The explanation as string and optional the best matching event sequence.
        """
        assert group in self._event_sequences

        _logger.debug('Explaining anomaly..')
        possible_sequences = self._event_sequences[group]
        reason = ''
        if anomaly.conditions not in possible_sequences:
            reason += '- The conditions of the event sequence are unknown by the system\n'
        else:
            # Check if weights are to low
            for event_sequence in possible_sequences[anomaly.conditions]:
                if not event_sequence.is_anomaly(anomaly, 0):
                    reason += '- Found a matching event sequence, but the weights were to low\n'
                    return reason, None

        # Check if any other conditions would create a match
        m: Tuple[Optional[EventSequence], Optional[FrozenSet[Condition]], bool] = None, None, False
        for conditions in possible_sequences:
            anomaly.conditions = conditions  # Fake the conditions for 100% matching
            for event_sequence in possible_sequences[conditions]:
                if not event_sequence.is_anomaly(anomaly, CONFIG.anomaly_weight_threshold):
                    m = event_sequence, conditions, False
                    break

                elif not event_sequence.is_anomaly(anomaly, 0):
                    m = event_sequence, conditions, True
                    break

            if m[0] is not None:
                break

        # Reset conditions
        anomaly.conditions = None  # This does not set conditions to None, it None`s the fake conditions

        if m[0] is not None:
            reason += '- The event sequence is known by the system, but the conditions do not match any of the known\n'
            if m[2]:
                reason += '  and the weights were too low\n'

            # Find the difference between conditions
            target = set(m[1]) - set(anomaly.conditions)
            actual = set(anomaly.conditions) - set(m[1])
            reason += f'- Changing conditions {", ".join([str(c) for c in actual])} to ' \
                      f'{", ".join([str(c) for c in target])}, would make disappear the anomaly\n'
            return reason, None

        # Find the best matching event sequence
        match_score = 0
        best_match: Optional[EventSequence] = None
        for conditions in possible_sequences:
            for event_sequence in possible_sequences[conditions]:
                score = event_sequence.get_similarity_score(anomaly)
                if score > match_score:
                    best_match = event_sequence
                    match_score = score

        if best_match:
            if anomaly in best_match:
                missing_event = best_match.nodes - anomaly.nodes
                reason += f'The event sequence is missing the following events: {missing_event}!'
            else:
                reason += f'- The best matching event sequence reached a score of {match_score:.2f} (max=2.0)\n'
                node_score = best_match.get_node_similarity(anomaly)
                edge_score = best_match.get_edge_similarity(anomaly)
                conditions_score = best_match.get_conditions_similarity(anomaly)
                reason += f'- {int(node_score*100)}% event similarity\n'
                reason += f'- {int(edge_score*100)}% event transition similarity\n'
                reason += f'- {int(conditions_score*100)}% condition similarity\n'

        return reason, best_match
