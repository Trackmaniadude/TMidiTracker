"""
Docstring for utils.tk
"""

if __name__ == "__main__":
    import sys

    sys.path.append(".")

import tkinter as tk
from dataclasses import dataclass, field
from tkinter import ttk
from typing import Any, Callable, Literal, cast

from utils.event import Event


class SPECIAL_CHARS:
    ARROW_DOWN = "▼"
    ARROW_UP = "▲"


DEF_PAD = 2


BLOCK_ERRANT_ENTRIES: list[type[tk.Misc]] = [
    tk.Entry,
    ttk.Entry,
    tk.Text,
    tk.Spinbox,
    ttk.Spinbox,
]


def blockEventFromTypes(
    func: Callable[[tk.Event], None],
    blockList: list[type[tk.Misc]] = BLOCK_ERRANT_ENTRIES,
):
    """Wrap a tk bind callback to block calling when certain types of widgets are in focus (if it is not doing that for some reason)"""
    classes = {c().winfo_class() for c in blockList}

    def wrapped(event: tk.Event):
        if event.widget.winfo_class() in classes:
            return
        func(event)

    return wrapped


def isDescendantOf(test: tk.Misc, descendsFrom: tk.Misc) -> bool:
    return str(test).startswith(str(descendsFrom))


def widgetUnderCursor(widget: tk.Misc):
    root = widget.winfo_toplevel()
    x, y = root.winfo_pointerxy()
    return root.winfo_containing(x, y)


def bindOnSizeChange(widget: tk.Misc, callback: Callable[[], None]):
    lastWidth = widget.winfo_width()
    lastHeight = widget.winfo_height()

    def _callback(*_):
        nonlocal lastWidth, lastHeight
        currentWidth = widget.winfo_width()
        currentHeight = widget.winfo_height()
        if currentWidth != lastWidth or currentHeight != lastHeight:
            lastWidth = currentWidth
            lastHeight = currentHeight
            callback()

    widget.bind("<Configure>", _callback, add=True)


@dataclass
class TKQueuedActionState:
    """Injected into an instance so TKQueuedAction can keep track of queue state."""

    queued: bool = False
    args: tuple[Any, ...] = field(default_factory=lambda: tuple())
    kwargs: dict[str, Any] = field(default_factory=lambda: dict())


class TKQueuedAction[A]:  # Not using the generic confuses pylance
    """
    Queue object created by tkQueueAction wrapper. Replaces a normal method function in a class.
    """

    def __init__(
        self, f: Callable[[A], None], argmode: Literal["first", "last"] = "last"
    ) -> None:
        self.function = f
        self.argmode = argmode
        self.__storename = f"__{self.__class__.__name__}-{id(self)}"

    def __get__(self, instance, owner):
        def f(*args, **kwargs):
            if not hasattr(instance, self.__storename):
                setattr(instance, self.__storename, TKQueuedActionState())
            state = getattr(instance, self.__storename)
            if state.queued:
                if self.argmode == "last":
                    state.args = args
                    state.kwargs = kwargs
            else:
                state.queued = True
                state.args = args
                state.kwargs = kwargs
                instance.after(
                    "idle",
                    lambda: (
                        self.function(instance, *state.args, **state.kwargs),
                        setattr(state, "queued", False),
                    ),
                )

        return f


def tkQueuedAction(argmode: Literal["first", "last"] = "last"):
    """
    A method wrapped with this will, when called, be queued for next tk idle stage.
    Subsequent calls will be ignored until tk gets around to it.

    WARNING: Calls may not return values.

    If the method has arguments, it will use the most recent attempt to call, unless
    argmode = "first", in which case it will use the args for the first call (since
    it was last queued.)
    """

    def dec(f):
        a = TKQueuedAction(f, argmode)
        return a

    return dec


tkvar = tk.StringVar | tk.IntVar | tk.BooleanVar | tk.DoubleVar
tkvart = str | int | bool | float


class TKVar[V: tkvar, VT: tkvart]:
    """Tk variable wrapper that uses a mirror value to detect changes coming from the interface."""

    def __init__(self, var: V, default: VT) -> None:
        self.var: V = var
        self.__mirror: VT = default

        self.var.trace_add("write", lambda *_: self.__trace())

        self.Changed: Event[[]] = Event(f"{self.__class__.__name__}.Changed")
        self.ChangedUser: Event[[]] = Event(f"{self.__class__.__name__}.ChangedUser")

    def __trace(self):
        actual = cast(VT, self.var.get())
        if self.__mirror != actual:
            self.__mirror = actual
            self.ChangedUser.fire()
        self.Changed.fire()

    def set(self, v: VT):
        self.__mirror = v
        self.var.set(v)  # pyright: ignore[reportArgumentType]

    def get(self) -> VT:
        return self.var.get()  # pyright: ignore[reportReturnType]


if __name__ == "__main__":
    root = tk.Tk()

    def testdec(f):
        return f

    # a = TKVar(tk.BooleanVar(), True)
    # aa = a.get()
    # b = TKVar(tk.StringVar(), "")
    # bb = a.get()

    class test(ttk.Frame):
        def __init__(self, parent: tk.Misc):
            super().__init__(parent)

        def t0(self, a: int = 1):
            """t0"""
            print(f"T0 {a}")

        @testdec
        def t1(self, a: int = 3):
            """t1"""
            print(f"T1 {a}")

        @tkQueuedAction("first")
        def t2(self, a: int = 5):
            """t2"""
            print(f"T2 {a}")

        @tkQueuedAction("last")
        def t3(self, a: int = 6):
            """t3"""
            print(f"T3 {a}")

        @tkQueuedAction()
        def t4(self, a: int = 6):
            """t4"""
            return f"T3 {a}"

    a = test(root)

    def testfunc():
        root.after(667, lambda: root.destroy())

        a.t0(1)
        a.t0(2)
        a.t0(3)
        a.t1(1)
        a.t1(2)
        a.t1(3)
        a.t2(1)
        a.t2(2)
        a.t2(3)
        a.t3(1)
        a.t3(2)
        a.t3(3)
        print(f"t4: {a.t4()}")
        root.update_idletasks()

    root.after(333, testfunc)

    root.mainloop()
