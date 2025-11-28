"""
Live playback code.
"""

import time
from threading import Event, Thread

from structures import program  # Note: Can't use during init


class Player:
    """
    Provides live playback of song data.
    """

    def __init__(self):

        self.resume = Event()

        self.matrixRow: int = 0
        """Current row in pattern matrix."""
        self.patternRow: int = 0
        """Current row within pattern."""

        def playbackDaemon():
            while True:
                self.resume.wait()

                tickLength = 1 / program.currentSong.clock
                ticks = program.currentSong.groove[0]

                print(time.time())

                time.sleep(tickLength * ticks)

        Thread(name="PlaybackDaemon", target=playbackDaemon, daemon=True).start()

    def setPlaybackCursor(self, matrixRow: int, patternRow: int):
        self.matrixRow = matrixRow
        self.patternRow = patternRow

    def play(self):
        self.resume.set()

    def pause(self):
        self.resume.clear()
