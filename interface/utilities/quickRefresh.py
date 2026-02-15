import random
from abc import ABC, abstractmethod


class QuickRefresh(ABC):
    """
    Adds a "queueRefresh" method, which will tell tk to call the object's "refresh" method when next possible.
    Uses a flag to avoid queuing multiple refreshes in one frame.
    """

    # def __init__(self) -> None:
    #     self._refreshQueueFlag: bool = False

    def queueRefresh(self):
        try:
            if not self._refreshQueueFlag:
                self._refreshQueueFlag = True
                self.after_idle(self.refresh)  # type: ignore
        except AttributeError:
            # TODO: figure out how to properly initialize the data (why isnt it working?)
            self._refreshQueueFlag = False

    def resetRefreshFlag(self):
        # TODO: is there a way to make this automatic?
        self._refreshQueueFlag = False

    @abstractmethod
    def refresh(self): ...
