# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import configparser
import logging

# Library Imports
# […]

# Project Imports
# […]

_logger = logging.getLogger(__name__)


class _Config:

    def __init__(self, filename: str) -> None:
        parser = configparser.ConfigParser()
        if not parser.read(filename):
            error_message = f'Could not read config file "{filename}"!'
            _logger.error(error_message)
            raise RuntimeError(error_message)

        # Default
        self._item_list = parser.get('DEFAULT', 'item_list')

        # Database
        self._database_engine = parser.get('DATABASE', 'engine')
        self._database_host = parser.get('DATABASE', 'host')
        self._database_port = parser.getint('DATABASE', 'port')
        self._database_user = parser.get('DATABASE', 'user')
        self._database_password = parser.get('DATABASE', 'password')
        self._database_name = parser.get('DATABASE', 'name')

        # Parameters
        self._t_init = parser.getint('PARAMETERS', 't_init')
        self._t_inc = parser.getint('PARAMETERS', 't_inc')
        self._t_inc_stable = parser.getint('PARAMETERS', 't_inc_stable')
        self._n = parser.getint('PARAMETERS', 'n')
        self._anomaly_weight_threshold = parser.getint('PARAMETERS', 'anomaly_weight_threshold')

    @property
    def item_list(self) -> str:
        return self._item_list

    @property
    def database_engine(self) -> str:
        return self._database_engine

    @property
    def database_host(self) -> str:
        return self._database_host

    @property
    def database_port(self) -> int:
        return self._database_port

    @property
    def database_user(self) -> str:
        return self._database_user

    @property
    def database_password(self) -> str:
        return self._database_password

    @property
    def database_name(self) -> str:
        return self._database_name

    @property
    def t_init(self) -> int:
        return self._t_init

    @property
    def t_inc(self) -> int:
        return self._t_inc

    @property
    def t_inc_stable(self) -> int:
        return self._t_inc_stable

    @property
    def n(self) -> int:
        return self._n

    @property
    def anomaly_weight_threshold(self) -> int:
        return self._anomaly_weight_threshold


CONFIG = _Config('config.ini')
