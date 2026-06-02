import tkinter as tk
from tkinter import ttk

from utils.misc import BracketDictAccess

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from interface.utilities.dictSettingsEditor import DictSettingsEditor
from interface.utilities.dictSettingsEditorEntries import DSEEntries
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures.settings import Settings
from utils.fluidsynth import FLUIDSYNTH_EXISTS


class SettingsView(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)

        self.sf = DScrollFrame(
            self, mode="VERTICAL", propagationMode="frameDrivesContent"
        )
        self.sf.pack(fill="both", expand=True)

        self.editor = DictSettingsEditor(
            self.sf.content, BracketDictAccess(Settings), autoApply=True
        )
        self.editor.pack(fill="both", expand=True)

        ################

        self.editor.addSubEditor("Directories").addValueEdit(
            "projectDirectory", DSEEntries.Folder(), "Projects"
        ).addValueEdit("exportDirectory", DSEEntries.Folder(), "Exports")

        self.editor.addSubEditor("Preferences").addValueEdit(
            "recentsLength", DSEEntries.Integer(min=1, max=50), "Max Recents"
        ).addValueEdit("defaultAuthor", DSEEntries.SmallTextbox(), "Default Author")

        if FLUIDSYNTH_EXISTS:
            self.editor.addSubEditor("Fluidsynth").addValueEdit(
                "soundfontDirectory", DSEEntries.Folder(), "Soundfonts"
            )


if __name__ == "__main__":

    root = tk.Tk()
    root.geometry("400x500")

    view = SettingsView(root)
    view.pack(fill="none", expand=False)

    root.mainloop()

    Settings.save()
