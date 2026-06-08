import logging
from importlib import import_module
from pathlib import Path

_logger = logging.getLogger(__name__)

paths = list()

# Collect effects for effect manager to collate

for p in Path(__file__).parent.iterdir():
    if not p.is_file():
        continue
    if not p.name.endswith(".py"):
        continue
    if p.samefile(Path(__file__)):
        continue
    _logger.info(f"Importing effect file {p.name}...")
    paths.append(str(p.name)[:-3])

__all__ = paths  # pyright: ignore[reportUnsupportedDunderAll]
