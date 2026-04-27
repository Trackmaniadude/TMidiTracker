"""
Storage for program configuration. More intended for remembering things between close and open than actual settings.
"""

import json
import logging
from typing import Any, Callable, Protocol

_logger = logging.getLogger(__name__)

PERSISTENCE_FILE = "PERSISTENCE"

USE_DEFAULT = object()
"""Passed to load handlers when the key is not present in the persistence file."""


class SAVE_FUNC[T](Protocol):
    def __call__(self) -> T: ...


class LOAD_FUNC[T](Protocol):
    def __call__(self, value: T): ...


handlers: dict[str, tuple[SAVE_FUNC, LOAD_FUNC]] = dict()


def loadPersistence():
    try:
        with open(PERSISTENCE_FILE, "r") as fp:
            data = json.load(fp)
            if type(data) is not dict:
                raise Exception("Top level persistence must be dict!")
            for key, (save, load) in handlers.items():
                try:
                    val = data[key]
                    load(val)
                except Exception as e:
                    _logger.warning(
                        f"Could not load key '{key}' from persistence: {e.__class__.__name__}: {e}"
                    )
                    load(USE_DEFAULT)
    except FileNotFoundError:
        pass
    except Exception as e:
        _logger.exception(e)


def savePersistence():
    try:
        with open(PERSISTENCE_FILE, "w") as fp:
            json.dump({key: save() for key, (save, load) in handlers.items()}, fp)
    except Exception as e:
        _logger.exception(e)


def registerPersistence[T](key: str, save: SAVE_FUNC[T], load: LOAD_FUNC[T]):
    handlers[key] = (save, load)


if __name__ == "__main__":
    val: int = 3

    def load(value: int):
        global val
        val = value if type(value) is int else 1

    def save() -> int:
        return val

    registerPersistence("val", save, load)
    print(val)
    loadPersistence()
    print(val)
    # savePersistence()
