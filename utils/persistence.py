import json
import logging
from typing import Protocol

_logger = logging.getLogger(__name__)

USE_DEFAULT = object()
"""Passed to load handlers when the key is not present in the persistence file."""


class SAVE_FUNC[T](Protocol):
    def __call__(self) -> T: ...


class LOAD_FUNC[T](Protocol):
    def __call__(self, value: T): ...


class Persistence:
    """
    Mixin(?) type storage handler. Anything that wants to save/load registers save/load handlers with this, which will be called
    when it needs to save/load. Primarily meant for configuration files and similar. Uses JSON under the hood, so values passed by
    load/passed to save must be convertible to JSON using the default converter.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.handlers: dict[str, tuple[SAVE_FUNC, LOAD_FUNC]] = dict()

    def loadPersistence(self):
        """Read values from the persistence file, and load them in (by calling their associated load functions)"""
        try:
            with open(self.filename, "r") as fp:
                data = json.load(fp)
                if type(data) is not dict:
                    raise Exception("Top level persistence must be dict!")
                for key, (save, load) in self.handlers.items():
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

    def savePersistence(self):
        """Save values to the persistence file (by calling their associated save functions)"""
        try:
            with open(self.filename, "w") as fp:
                json.dump(
                    {key: save() for key, (save, load) in self.handlers.items()},
                    fp,
                    indent=3,
                )
        except Exception as e:
            _logger.exception(e)

    def registerPersistence[T](self, key: str, save: SAVE_FUNC[T], load: LOAD_FUNC[T]):
        """
        Register a persistence value.

        Save should be a callable returning an object that can be serialized by the default JSON serializer.

        load should be a callable that takes in the same value that save returns.

        load will be supplied with USE_DEFAULT if it's key is missing from persistence. (I have no idea how to type hint that)
        """
        self.handlers[key] = (save, load)


if __name__ == "__main__":
    val: int = 1

    p = Persistence("testpersistence.txt")

    def load(value: int):
        global val
        val = value if type(value) is int else 1

    def save() -> int:
        return val

    p.registerPersistence("val", save, load)
    print(val)
    p.loadPersistence()
    print(val)
    p.savePersistence()
