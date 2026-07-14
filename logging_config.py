"""Console logging setup for the desktop GUI process.

Call setup_logging() once, before creating the QApplication, so that any
module can just do `logging.getLogger(__name__)` and have output show up
consistently instead of relying on stray print()s.
"""

import logging


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
