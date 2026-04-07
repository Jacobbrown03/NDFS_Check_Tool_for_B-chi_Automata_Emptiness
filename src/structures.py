# Put the main data structures here
# Likely need:
# TransitionSystem
# BuchiAutomaton
# ProductAutomaton
# NDFSResult

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional


LabelSet = frozenset[str]
ProductState = Tuple[str, str]


@dataclass
class TransitionSystem:
    states: Set[str]
    transitions: Dict[str, Set[str]]
    initial_state: str
    labels: Dict[str, Set[str]]
    accepting_states: Set[str] = field(default_factory=set)

    def successors(self, state: str) -> Set[str]:
        return self.transitions.get(state, set())

    def label_of(self, state: str) -> Set[str]:
        return self.labels.get(state, set())


@dataclass
class BuchiAutomaton:
    states: Set[str]
    initial_state: str
    accepting_states: Set[str]
    transitions: Dict[Tuple[str, LabelSet], Set[str]]
    alphabet: Set[LabelSet] = field(default_factory=set)

    def next_states(self, state: str, label: Set[str]) -> Set[str]:
        key = (state, frozenset(label))
        return self.transitions.get(key, set())


@dataclass
class ProductAutomaton:
    states: Set[ProductState]
    initial_state: Set[ProductState]
    accepting_states: Set[ProductState]
    transitions: Dict[ProductState, Set[ProductState]]

    def successors(self, state: ProductState) -> Set[ProductState]:
        return self.transitions.get(state, set())


@dataclass
class NDFSResult:
    accepting_cycle_found: bool
    witness_prefix: List[ProductState] = field(default_factory=list)
    witness_cycle: List[ProductState] = field(default_factory=list)
    visited_blue: Set[ProductState] = field(default_factory=set)
    visited_red: Set[ProductState] = field(default_factory=set) 
    
