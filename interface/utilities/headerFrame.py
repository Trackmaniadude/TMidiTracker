import tkinter as tk
from tkinter import ttk

from utils.tk import DEF_PAD, SPECIAL_CHARS


class HeaderFrame(ttk.Frame):
    def __init__(
        self, parent: tk.Misc, label: str, *, userCollapsible: bool = False, **kwargs
    ):
        super().__init__(parent, **kwargs)

        # Body

        self.header = ttk.Frame(self, padding=DEF_PAD)
        self.header.pack(side="top", fill="x", expand=False)

        self.separator = ttk.Separator(self, orient="horizontal")
        self.separator.pack(side="top", fill="x", expand=False)

        self.content = ttk.Frame(self, padding=DEF_PAD)
        self.content.pack(side="top", fill="x", expand=False)

        # Header

        self.label = ttk.Label(self.header, text=label)
        self.label.pack(side="left", fill="y", expand=False)

        self.collapseButton = ttk.Button(
            self.header, text=SPECIAL_CHARS.ARROW_DOWN, width=2, command=self.collapse
        )
        if userCollapsible:
            self.collapseButton.pack(side="right", fill="y", expand=False)

    def collapse(self):
        self.content.pack_forget()
        self.collapseButton.config(text=SPECIAL_CHARS.ARROW_UP, command=self.expand)

    def expand(self):
        self.content.pack(side="top", fill="x", expand=False)
        self.collapseButton.config(text=SPECIAL_CHARS.ARROW_DOWN, command=self.collapse)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")

    testFrame1 = HeaderFrame(root, "testFrame1", userCollapsible=True)
    testFrame1.pack(side="top", fill="both", expand=True)

    tk.Frame(testFrame1.content, width=50, height=50, background="#00AAFF").pack(
        side="top", fill="none", expand=False
    )

    root.mainloop()
