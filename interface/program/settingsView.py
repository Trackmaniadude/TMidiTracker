import tkinter as tk
from tkinter import ttk

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from interface.utilities.dictSettingsEditor import DictSettingsEditor
from interface.utilities.dictSettingsEditorEntries import DSEEntries
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures.settings import Settings
from utils.fluidsynth import FLUIDSYNTH_EXISTS
from utils.misc import BracketDictAccess


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

        dirEdit = self.editor.addSubEditor("Directories")
        dirEdit.addValueEdit(
            "projectDirectory", DSEEntries.Folder(), "Projects"
        ).addTooltip("Initial directory to show in file explorer when saving projects.")
        dirEdit.addValueEdit(
            "exportDirectory", DSEEntries.Folder(), "Exports"
        ).addTooltip(
            "Initial directory to show in file explorer when exporting projects."
        )

        prefEdit = self.editor.addSubEditor("Preferences")
        prefEdit.addValueEdit(
            "recentsLength", DSEEntries.Integer(min=1, max=50), "Max Recents"
        ).addTooltip("How many recently opened files to remember and display.")
        prefEdit.addValueEdit(
            "defaultAuthor", DSEEntries.SmallTextbox(), "Default Author"
        ).addTooltip("Default entry for the project's 'Author' field.")

        ################

        if FLUIDSYNTH_EXISTS:
            fonts = {
                "USE LAST": "Last",
                None: "Internal",
            }
            for child in Settings.soundfontDirectory.iterdir():
                if not child.is_file():
                    return
                if not child.name.endswith(".sf2"):
                    return
                fonts[child] = str(child.name)
            fsEdit = self.editor.addSubEditor("Fluidsynth")
            fsEdit.addValueEdit(
                "soundfontDirectory", DSEEntries.Folder(), "Soundfonts"
            ).addTooltip("Directory to scan for soundfonts in.")
            fsEdit.addValueEdit(
                "preferredSoundfont",
                DSEEntries.List(values=fonts),
                "Preferred Soundfont",
            ).addTooltip("Which soundfont to select when the program is started.")


if __name__ == "__main__":

    root = tk.Tk()
    root.geometry("400x500")

    view = SettingsView(root)
    view.pack(fill="both", expand=True)

    root.mainloop()

    Settings.save()
