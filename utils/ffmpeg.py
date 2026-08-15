import logging
import shutil
import sys
from pathlib import Path
from subprocess import run

_logger = logging.getLogger(__name__)


FFMPEG_COMMAND = "ffmpeg"
FFMPEG_EXISTS = shutil.which(FFMPEG_COMMAND) is not None
if "--no-ffmpeg" in sys.argv:
    FFMPEG_EXISTS = False


def quickConvert(from_: Path, to: Path):
    _logger.debug(f"Using FFMPEG to convert {from_} to {to}")
    cmd = [FFMPEG_COMMAND, "-y", "-i", str(from_.resolve()), str(to.resolve())]
    run(cmd).check_returncode()


if __name__ == "__main__":
    print(FFMPEG_EXISTS)
