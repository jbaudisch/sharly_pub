# Future Imports
from __future__ import annotations

# Typing Imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *

# Builtin Imports
import argparse
import logging

# Library Imports
# […]

# Project Imports
from sharly.application.learn import LearnApplication
from sharly.util.logging import setup_logger

_logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='enable verbose output', action='store_true')
    parser.add_argument('-d', '--debug', help='enable debug logging', action='store_true')
    parser.add_argument('-i', '--interval', help='learning interval in days', default=7, type=int)
    parser.add_argument('-vi', '--visualize', help='visualize final event sequences', action='store_true')
    parser.add_argument('-vz', '--visualize_zero_edges', help='visualize zero weight edges', action='store_true')
    parser.add_argument('-p', '--plot', help='plot learning graphs', action='store_true')
    args = parser.parse_args()

    setup_logger(args.verbose, args.debug)

    with LearnApplication(args.interval) as app:
        app.start(args.visualize, args.visualize_zero_edges, args.plot)


if __name__ == '__main__':
    main()
