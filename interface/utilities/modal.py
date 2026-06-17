import tkinter as tk
from tkinter import ttk


class Modal(tk.Toplevel):
    def __init__(
        self, parent, title: str = "Modal Dialog", allowManualClose: bool = False
    ):
        super().__init__(parent)

        self.allowClose = allowManualClose

        self.title(title)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.__close_modal)
        self.grab_set()

    def __close_modal(self):
        if not self.allowClose:
            return
        else:
            self.bell()
        self.destroy()

    def destroy(self) -> None:
        self.allowClose = True
        self.grab_release()
        return super().destroy()
