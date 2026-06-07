"""View and edit song metadata."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from interface.utilities.dictSettingsEditor import DictSettingsEditor
from interface.utilities.dictSettingsEditorEntries import DSEEntries
from interface.utilities.doubleScrollFrame import DScrollFrame
from interface.utilities.headerFrame import HeaderFrame
from interface.utilities.validatedEntry import Validators
from interface.utilities.validatedEntryPrebuilts import Prebuilts
from structures import program
from structures.globalEvents import SongReloaded, StructureChanged, TimingChanged
from structures.settings import Settings
from utils.event import Connection
from utils.fluidsynth import FLUIDSYNTH_EXISTS


class SongDataView(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=300, height=0, borderwidth=2)

        self.pack_propagate(False)

        sf = DScrollFrame(self, mode="VERTICAL", propagationMode="frameDrivesContent")
        sf.pack(fill="both", expand=True)
        self.content = sf.content

        self.connections: list[Connection] = list()

        ### Metadata
        metadataEdit = DictSettingsEditor(
            self.content,
            program.p.currentSong.metadata.__dict__,
            "Metadata",
            autoApply=True,
            collapsible=True,
        )

        def doMetadataEdit():
            metadataEdit.pack(side="top", fill="x", expand=False)
            metadataEdit.addValueEdit("title", DSEEntries.SmallTextbox(), "Title")
            metadataEdit.addValueEdit("author", DSEEntries.SmallTextbox(), "Author")
            metadataEdit.addValueEdit("genre", DSEEntries.SmallTextbox(), "Genre")
            metadataEdit.addValueEdit("notes", DSEEntries.LargeTextbox(), "Notes")

        doMetadataEdit()

        ### Timing
        timeEdit = DictSettingsEditor(
            self.content,
            program.p.currentSong.__dict__,
            "Time/Speed",
            autoApply=True,
            collapsible=True,
        )

        def doTimeEdit():
            def grooveTFIn(l: list[int]) -> str:
                return " ".join(str(e) for e in l)

            def grooveTFOut(s: str) -> list[int]:
                return [int(e) for e in s.split(" ")]

            def grooveValid(s: str) -> str | None:
                try:
                    grooveTFOut(s)
                except:
                    return None
                else:
                    return s

            timeEdit.pack(side="top", fill="x", expand=False)
            timeEdit.addValueEdit(
                "clock",
                DSEEntries.Float(min=1, max=1000),
                "Clock (hz)",
            )
            timeEdit.addValueEdit(
                "groove",
                DSEEntries.SmallTextbox(validator=Validators.Function(grooveValid)),
                label="Groove",
                transformIn=grooveTFIn,
                transformOut=grooveTFOut,
            )
            timeEdit.addTextbox(
                "Ticks to run before stepping to the next row. Can have multiple values to use different timings per row."
                "Ex: '6 4' will have every other row be shorter, which can be useful for swing."
            )
            timeEdit.addValueEdit(
                "loopCount",
                DSEEntries.Integer(min=1),
                "Loop Count",
            )
            timeEdit.addTextbox(
                "Loop count overrides indefinite loops during export (or other offline playback)."
            )
            timeEdit.Applied.connect(
                lambda changes: TimingChanged.fire(changes), self.connections
            )

        doTimeEdit()

        ### Structure
        structureEdit = DictSettingsEditor(
            self.content,
            program.p.currentSong.__dict__,
            "Song Structure",
            autoApply=True,
            collapsible=True,
        )

        def doStructureEdit():
            # structureEdit.collapse()
            structureEdit.pack(side="top", fill="x", expand=False)
            structureEdit.addValueEdit(
                "visibleChannels", DSEEntries.Integer(min=0, max=14), "Pitched Channels"
            )
            structureEdit.addValueEdit(
                "patternLength", DSEEntries.Integer(min=1, max=255), "Pattern Size"
            )
            structureEdit.addValueEdit(
                "majorSubdiv", DSEEntries.Integer(min=1, max=10000), "Major Subdivision"
            )
            structureEdit.addValueEdit(
                "minorSubdiv",
                DSEEntries.Integer(min=1, max=10000),
                "Minor Subdivision",
            )
            structureEdit.Applied.connect(
                lambda changes: StructureChanged.fire(changes), self.connections
            )

        doStructureEdit()

        ### Fluidsynth
        fsEdit = None
        if FLUIDSYNTH_EXISTS:
            fsEdit = DictSettingsEditor(
                self.content,
                program.p.currentSong.__dict__,
                "Fluidsynth",
                autoApply=True,
                collapsible=True,
            )

            def doFsEdit():
                fsEdit.pack(side="top", fill="x", expand=False)

                fonts: dict[None | Path, str] = {
                    None: "None",
                }
                for child in Settings.soundfontDirectory.iterdir():
                    if not child.is_file():
                        return
                    if not child.name.endswith(".sf2"):
                        return
                    fonts[child] = str(child.name)

                fsEdit.addValueEdit(
                    "preferredSoundfont",
                    DSEEntries.List(values=fonts),
                    "Preferred Soundfont",
                )

            doFsEdit()

        # Rebinding
        def reload():
            metadataEdit.rebind(program.p.currentSong.metadata.__dict__)
            metadataEdit.revert()
            timeEdit.rebind(program.p.currentSong.__dict__)
            timeEdit.revert()
            structureEdit.rebind(program.p.currentSong.__dict__)
            structureEdit.revert()
            if fsEdit is not None:
                fsEdit.rebind(program.p.currentSong.__dict__)
                fsEdit.revert()

        SongReloaded.connect(lambda *_: reload(), self.connections)

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()
