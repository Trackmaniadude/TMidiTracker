import json
import logging
from pathlib import Path
from typing import Any, Literal

_logger = logging.getLogger(__name__)

SETTINGS_FILE = Path("SETTINGS")


class Settings:
    """
    Program configuration.
    """

    # TODO: settingsview should have the ability to gather tooltips from docs?

    # Directories
    exportDirectory: Path = Path("exports")
    projectDirectory: Path = Path("projects")

    # User Preferences
    recentsLength: int = 10
    defaultAuthor: str = ""

    # Fluidsynth Specific
    soundfontDirectory: Path = Path("soundfonts")
    preferredSoundfont: None | Path | Literal["USE LAST"] = "USE LAST"

    @classmethod
    def overrideLoad(cls, key: str, t: type, value: Any) -> bool:
        """Keys that require special handling go here. Returns true if it handled anything."""
        if key == "preferredSoundfont":
            if value is None:
                cls.preferredSoundfont = None
            elif value == "USE LAST":
                cls.preferredSoundfont = "USE LAST"
            else:
                cls.preferredSoundfont = Path(value)
            return True
        return False

    @classmethod
    def save(cls):
        def default(value: object):
            if isinstance(value, Path):
                return str(value)

        with open(SETTINGS_FILE, "w") as file:
            json.dump(
                {
                    k: v
                    for k, v in cls.__dict__.copy().items()
                    if k in cls.__annotations__
                },
                file,
                default=default,
                indent=4,
            )

    @classmethod
    def load(cls):
        if not SETTINGS_FILE.exists():
            return

        try:
            with open(SETTINGS_FILE, "r") as file:
                dct: dict[str, Any] = json.load(file)
        except Exception as e:
            _logger.exception(e)
        else:
            for key, value in dct.items():
                t = cls.__annotations__.get(key)
                if t is None:
                    continue
                if cls.overrideLoad(key, t, value):
                    continue
                if t is Path:
                    setattr(cls, key, Path(value))
                else:
                    setattr(cls, key, value)


s = Settings
s.load()
