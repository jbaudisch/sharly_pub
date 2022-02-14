# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from sharly.database import Database

# Builtin Imports
import logging

# Library Imports
# […]

# Project Imports
from sharly.database.sqlite import SQLiteDatabase

_logger = logging.getLogger(__name__)


class DatabaseFactory:
    @classmethod
    def get_database(cls, engine: str, *args: Any, **kwargs: Any) -> Database:
        if engine == 'sqlite':
            return SQLiteDatabase(*args, **kwargs)
        else:
            error_message = f'Unknown database engine "{engine}"!'
            _logger.error(error_message)
            raise NotImplementedError(error_message)
