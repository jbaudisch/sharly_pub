# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import abc
import logging

# Library Imports
# […]

# Project Imports
# […]

_logger = logging.getLogger(__name__)


class Application(abc.ABC):
    def __enter__(self) -> Application:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    @abc.abstractmethod
    def start(self, *args: Any, **kwargs: Any) -> None:
        """Start the application."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop the application."""
