import logging
import shutil
import time
from pathlib import Path
from subprocess import PIPE, Popen
from uuid import uuid4

_logger = logging.getLogger(__name__)

FLUIDSYNTH_COMMAND = "fluidsynth"
FLUIDSYNTH_EXISTS = shutil.which(FLUIDSYNTH_COMMAND) is not None


class Fluidsynth:
    """Utility class that starts a Fluidsynth process and allows communicating with it."""

    def __init__(self, portName: str | None = None) -> None:
        _logger.debug("Setting up Fluidsynth")

        # Start fluidsynth
        path = shutil.which(FLUIDSYNTH_COMMAND)
        if path is None:
            raise FileNotFoundError("Unable to find Fluidsynth. Is it installed?")

        self.portName = (
            portName if portName is not None else f"Internal-Fluidsynth-{uuid4()}"
        )
        self.process = Popen(
            [path, "-p", self.portName, "--quiet", "-g", "0.7"],
            stdin=PIPE,
            stdout=PIPE,
            text=True,
        )

        # Font setting
        self.fontIndex = 1
        self.lastLoadedSoundfont: Path | None = None

    def __enter__(self):
        return self

    def setGain(self, gain: float):
        gain = max(0, min(5, gain))
        self._interact(f"gain {gain}")

    def close(self):
        _logger.debug("Closing Fluidsynth")
        self._interact("quit")

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def loadSoundfont(self, path: Path):
        if not path.exists():
            return  # TODO: tell user?
        self._interact(f"unload {self.fontIndex}")
        self._interact(f'load "{path.resolve()}"')
        self.fontIndex += 1
        self.lastLoadedSoundfont = path

    def _interact(self, command: str):
        if self.process.stdin is None:
            return
        self.process.stdin.write(f"{command}\n")
        self.process.stdin.flush()

    def __str__(self) -> str:
        return f"Fluidsynth({self.portName})"

    def reset(self):
        self._interact("reset")


if __name__ == "__main__":
    with Fluidsynth() as fs:
        print(fs)
        time.sleep(2)
