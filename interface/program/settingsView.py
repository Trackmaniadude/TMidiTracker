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

        self.editor.addSubEditor("Directories").addValueEdit(
            "projectDirectory", DSEEntries.Folder(), "Projects"
        ).addValueEdit("exportDirectory", DSEEntries.Folder(), "Exports")

        self.editor.addSubEditor("Preferences").addValueEdit(
            "recentsLength", DSEEntries.Integer(min=1, max=50), "Max Recents"
        ).addValueEdit("defaultAuthor", DSEEntries.SmallTextbox(), "Default Author")

        ################

        if FLUIDSYNTH_EXISTS:
            fonts = ["Last", "Internal"]
            lookup = {
                "Last": "USE LAST",
                "Internal": None,
            }
            lookdown = {
                "USE LAST": "Last",
                None: "Internal",
            }
            for child in Settings.soundfontDirectory.iterdir():
                if not child.is_file():
                    return
                if not child.name.endswith(".sf2"):
                    return
                dir = str(child.name)
                fonts.append(dir)
                lookup[dir] = child
                lookdown[child] = dir
            self.editor.addSubEditor("Fluidsynth").addValueEdit(
                "soundfontDirectory", DSEEntries.Folder(), "Soundfonts"
            ).addValueEdit(
                "preferredSoundfont",
                DSEEntries.List(values=fonts),
                "Preferred Soundfont",
                transformIn=lambda v: lookdown.get(v, "Last"),
                transformOut=lambda v: (lookup.get(v, "USE LAST")),
            )


if __name__ == "__main__":

    root = tk.Tk()
    root.geometry("400x500")

    view = SettingsView(root)
    view.pack(fill="both", expand=True)

    root.mainloop()

    Settings.save()
