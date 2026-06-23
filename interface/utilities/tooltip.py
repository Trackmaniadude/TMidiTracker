import tkinter as tk
from tkinter import ttk
from typing import cast

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from interface import theme


class Tooltip:
    def __init__(
        self,
        owner: tk.Misc,
        text: str,
        *,
        triggerOnHover: bool = True,
        cursorOnHover: bool = True,
        clickDismisses: bool = True,
        hoverTimer: float = 0.75,
        maxWidth: int = 200,
        edgeAvoidance: int = 20,
        offset: int = 20,
    ) -> None:
        self.__owner = owner
        self.__window: tk.Toplevel | None = None
        self.__clickDismisses = clickDismisses
        self.__maxWidth = maxWidth
        self.__edgeAvoidance = edgeAvoidance
        self.__offset = offset
        self.text = text

        self.__triggerOnHover = triggerOnHover
        self.__enterDelay: str = ""
        self.__exitDelay: str = ""
        self.__hoverTimer = int(hoverTimer * 1000)

        if triggerOnHover:
            if cursorOnHover:
                self.__owner.config(cursor="question_arrow")  # type: ignore

            def onEnter():
                try:
                    self.__owner.after_cancel(self.__exitDelay)
                except ValueError:
                    pass  # Easiest way to let us do this even if its not needed
                self.__enterDelay = self.__owner.after(self.__hoverTimer, self.show)

            def onExit():
                try:
                    self.__owner.after_cancel(self.__enterDelay)
                except ValueError:
                    pass  # Easiest way to let us do this even if its not needed
                self.__exitDelay = self.__owner.after(self.__hoverTimer, self.hide)

            owner.bind("<Enter>", lambda *_: onEnter())
            owner.bind("<Leave>", lambda *_: onExit())

    def __createWindow(self):
        window = tk.Toplevel()
        window.transient(self.__owner.winfo_toplevel())
        window.geometry("1000x1000+2300+500")
        window.overrideredirect(True)

        label = ttk.Label(
            window, text=self.text, width=0, padding=4, wraplength=self.__maxWidth
        )
        label.pack()
        label.configure(style=cast(str, theme.Tooltip.StickyNote))

        window.update()  # Required for the label to place itself so we can get its size.

        # Calculate position
        width = label.winfo_width() + 4
        height = label.winfo_height() + 4

        screenWidth = label.winfo_screenwidth()
        screenHeight = label.winfo_screenheight()

        x = label.winfo_pointerx() + self.__offset
        y = label.winfo_pointery() + self.__offset

        # If tooltip would go off screen, move back
        x -= max(0, (x + width + self.__edgeAvoidance) - screenWidth)
        y -= max(0, (y + height + self.__edgeAvoidance) - screenHeight)

        geo = f"{label.winfo_width()}x{label.winfo_height()}+{x}+{y}"
        window.geometry(geo)

        # Events

        if self.__clickDismisses:
            label.bind_all("<Button-1>", lambda *_: self.hide(), "+")

        if self.__triggerOnHover:

            def onEnter():
                try:
                    self.__owner.after_cancel(self.__exitDelay)
                except ValueError:
                    pass  # Easiest way to let us do this even if its not needed

            def onExit():
                self.__exitDelay = self.__owner.after(self.__hoverTimer, self.hide)

            label.bind("<Enter>", lambda *_: onEnter())
            label.bind("<Leave>", lambda *_: onExit())

        return window

    def show(self):
        if self.__window is not None:
            return
        self.__window = self.__createWindow()

    def hide(self):
        if self.__window is None:
            return
        self.__window.destroy()
        self.__window = None


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x400")
    theme.generate()

    a = ttk.Button(root, text="Hover Tooltip", command=lambda: print("A"))
    a.pack()

    at = Tooltip(a, "Prints the letter A.")

    b = ttk.Button(root, text="Trigger Tooltip")
    b.pack()

    bt = Tooltip(b, "Makes this tooltip show. \n\n\n Long text!", triggerOnHover=False)
    b.config(command=lambda: bt.show())

    root.mainloop()
