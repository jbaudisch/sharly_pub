# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from sharly.model.condition import Condition

# Builtin Imports
import logging
import os

# Library Imports
logging.getLogger('matplotlib').setLevel(logging.ERROR)
import networkx
import matplotlib.pyplot

# Project Imports
from sharly.model.event import Event

_logger = logging.getLogger(__name__)


class EventSequence(networkx.DiGraph):
    """An event sequence is a sequence of events that occurs within T seconds of a previous event."""
    def __init__(self, id: Optional[int] = None) -> None:
        super().__init__()
        self._id = id
        self._fake_conditions = None

    @property
    def id(self) -> int:
        if self._id is None:
            raise ValueError(f'{self} has not id!')
        return self._id

    @property
    def root(self) -> Optional[Event]:
        try:
            return list(self)[0]
        except IndexError:
            return None

    @property
    def predecessor(self) -> Optional[Event]:
        try:
            return list(self)[-1]
        except IndexError:
            return None

    @property
    def conditions(self) -> FrozenSet[Condition]:
        if self._fake_conditions is not None:
            return self._fake_conditions

        try:
            return self.root.conditions
        except AttributeError:
            return frozenset()

    @conditions.setter
    def conditions(self, conditions: FrozenSet[Condition]) -> None:
        self._fake_conditions = conditions

    def __str__(self) -> str:
        if not self.edges:
            return str([node for node in self.nodes])
        return str([edge for edge in self.edges])

    def __contains__(self, item: Union[Event, EventSequence]) -> bool:
        if isinstance(item, Event):
            return super().__contains__(item)

        if self.conditions != item.conditions:
            return False

        self_edges = frozenset([(u, v) for u, v, w in self.edges(data='weight') if w > 0])
        item_edges = frozenset([(u, v) for u, v, w in item.edges(data='weight') if w > 0])

        self_nodes = frozenset(self.nodes)
        item_nodes = frozenset(item.nodes)

        return self_nodes >= item_nodes and self_edges >= item_edges

    def __eq__(self, other: EventSequence) -> bool:
        if self.conditions != other.conditions:
            return False

        self_nodes = frozenset(self.nodes)
        other_nodes = frozenset(other.nodes)
        if self_nodes != other_nodes:
            return False

        self_edges = frozenset([(u, v) for u, v, w in self.edges(data='weight') if w > 0])
        other_edges = frozenset([(u, v) for u, v, w in other.edges(data='weight') if w > 0])
        return self_edges == other_edges

    def __add__(self, other: EventSequence) -> EventSequence:
        if other != self:
            raise ValueError('Could not add incompatible event sequences!')

        merged_sequence = self.copy()
        for event, data in other.nodes(data=True):
            if self.has_node(event):
                merged_sequence.nodes[event]['occurrence'] += data['occurrence']

        for event_u, event_v, data in other.edges(data=True):
            if self.has_edge(event_u, event_v):
                merged_sequence[event_u][event_v]['weight'] += data['weight']

        return merged_sequence

    def add_event(self, event: Event, event_delay: int) -> bool:
        """Add an event to the sequence.

        Event sequences may include events from more than one user because a typical
        smart home has multiple users. Those events should be treated as noise.
        It is not possible to directly detect those noisy events.
        What is done instead, is that this method builds all "combinations" of events in an event sequence.
        Let's consider we have an event sequence: S = [0 -> 1 -> 2] where E=1 is sensor noise.
        So the essential sequence we would like to learn later is S = [0 -> 2]. To achieve this we simply
        add an edge between E=0 and E=2. We doing this on adding a new event and connect it with all predecessors.
        Now there is an edge between E=0 and E=2. And if this sequence occurs often, the edge-weight gets increased.

        Parameters
        ----------
        event
            The event to add.
        event_delay
            The maximum allowed delay between two events.
        Returns
        -------
        True, if the event was added, False otherwise.
        """
        if event in self:
            return False

        if self.predecessor:
            if (event.timestamp - self.predecessor.timestamp).total_seconds() > event_delay:
                return False

        predecessor = self.predecessor  # store predecessor before adding new node
        self.add_node(event, occurrence=1)

        if predecessor:
            self.add_edge(predecessor, event, weight=1)

            # Combinations (see docstring):
            predecessors = [e for e in self.nodes if e not in (event, predecessor)]
            for p in predecessors:
                # Zero weight because it is (for now) a virtual edge.
                # Might change after merging with other event sequences.
                self.add_edge(p, event, weight=0)

        return True

    def is_anomaly(self, other: EventSequence, w: int) -> bool:
        """Check if other is an anomaly in consideration against self.

        Parameters
        ----------
        other : EventSequence
            The event sequence to check against self.
        w : int
            The weight of an edge which is required to be no anomaly-edge.

        Returns
        -------
        True, if other is anomaly against self.
        """
        if other != self:
            return True

        for event_u, event_v, weight in other.edges(data='weight'):
            if self.has_edge(event_u, event_v):
                if weight:
                    if self[event_u][event_v]['weight'] < w:
                        return True

        return False

    def get_similarity_score(self, other: EventSequence) -> float:
        node_score = self.get_node_similarity(other)
        edge_score = self.get_edge_similarity(other)
        conditions_score = self.get_conditions_similarity(other)
        return ((3 * edge_score) + (2 * conditions_score) + node_score) / 3

    def get_node_similarity(self, other: EventSequence) -> float:
        self_nodes = frozenset(self.nodes)
        other_nodes = frozenset(other.nodes)
        common_nodes = self_nodes & other_nodes
        try:
            return len(common_nodes) / other.number_of_nodes()
        except ZeroDivisionError:
            return 0.0

    def get_edge_similarity(self, other: EventSequence) -> float:
        self_edges = frozenset(self.edges)
        other_edges = frozenset([(u, v) for u, v, w in other.edges(data='weight') if w > 0])
        common_edges = self_edges & other_edges
        try:
            return len(common_edges) / other.number_of_edges()
        except ZeroDivisionError:
            return 0.0

    def get_conditions_similarity(self, other: EventSequence) -> float:
        self_conditions = frozenset(self.conditions)
        other_conditions = frozenset(other.conditions)
        common_conditions = self_conditions & other_conditions
        try:
            return len(common_conditions) / len(other.conditions)
        except ZeroDivisionError:
            return 0.0

    def visualize(self, filename: str, visualize_zero_edges: bool = False, explanation: str = None) -> None:
        """Store the event sequence as image.

        Parameters
        ----------
        filename
            The name of the image (without extension).
        visualize_zero_edges
            Visualize zero-weight edges (default = False).
        explanation
            The explanation of the event sequence (e.g. why it is an anomaly etc.).
        """
        figure = matplotlib.pyplot.figure(figsize=(19.2, 10.8), dpi=80)

        # draw condition text
        conditions_text = ', '.join([str(c) for c in self.root.conditions])
        figure.text(.5, .05, conditions_text, ha='center', font={'size': 8})

        # draw graph
        node_positions = networkx.circular_layout(self)

        node_colors = ['#1f78b4' if node != self.root else '#009a00' for node in self]
        networkx.draw_networkx_nodes(self, node_positions, node_color=node_colors, node_size=400)

        if visualize_zero_edges:
            pseudo_edges = [(u, v) for u, v, d in self.edges(data=True) if d['weight'] == 0]
            networkx.draw_networkx_edges(self, node_positions, edgelist=pseudo_edges, edge_color='#a9a9a9',
                                         style='dotted', alpha=.5)

        real_edges = [(u, v) for u, v, d in self.edges(data=True) if d['weight'] > 0]
        networkx.draw_networkx_edges(self, node_positions, edgelist=real_edges, edge_color='#a9a9a9')

        node_labels = {n: f'{n}\n{o}' for n, o in networkx.get_node_attributes(self, 'occurrence').items()}
        networkx.draw_networkx_labels(self, node_positions, labels=node_labels, font_size=8, font_weight='bold')

        edge_labels = {(u, v): w for (u, v), w in networkx.get_edge_attributes(self, 'weight').items() if w > 0}
        networkx.draw_networkx_edge_labels(self, node_positions, edge_labels=edge_labels, font_size=8, label_pos=.25)

        matplotlib.pyplot.axis('off')

        image_filename = f'data/visualization/{filename}.jpg'
        tokens = image_filename.split('/')
        raw_path = '/'.join(tokens[:-1])
        if not os.path.exists(raw_path):
            os.makedirs(raw_path)

        matplotlib.pyplot.margins(x=0.3, y=0.3)
        matplotlib.pyplot.savefig(image_filename)
        matplotlib.pyplot.close()

        if explanation:
            text_filename = f'data/visualization/{filename}.txt'
            with open(text_filename, 'w') as f:
                f.write(explanation)
