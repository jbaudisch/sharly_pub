# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import logging
import sys

# Library Imports
# […]

# Project Imports
# […]

_logger = logging.getLogger(__name__)


def setup_logger(verbose: bool, debug: bool) -> None:
    """Setup default logger.

    Parameters
    ----------
    verbose : bool
        Enable (True)/Disable (False) verbose logging.
    debug : bool
        Enable (True)/Disable (False) debug logging.
    """
    level = logging.DEBUG if debug else logging.INFO
    fmt = '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
    datefmt = '%d. %b %Y %H:%M:%S'
    handlers = [
        logging.FileHandler('sys.log', mode='w'),
    ]
    if verbose:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(level=level, format=fmt, datefmt=datefmt, handlers=handlers)
