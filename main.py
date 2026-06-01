import argparse
import logging
import random
import tkinter as tk
import traceback
from enum import Enum
from pathlib import Path
from tkinter import filedialog, font, messagebox, ttk

import mido

from interface.program.channelDebug import ChannelDebug
from interface.program.effectList import EffectList
from interface.program.instrumentList import InstrumentList
from interface.program.patternList import PatternList
from interface.program.patternMatrix import PatternMatrix
from interface.program.patternViewFrame import PatternViewFrame
from interface.program.songDataView import SongDataView
from structures import program  # This also inits the program object
from structures.globalEvents import Copy, Cut, Paste, ProjectModified
from structures.player import Player
from structures.song import Song
from utils.constants import (
    CHANNEL_COUNT,
    MIDI_FILE_EXTENSION,
    MIDI_FILE_TK_LIST,
    PROGRAM_NAME,
    PROJECT_FILE_EXTENSION,
    PROJECT_FILE_TK_LIST,
    RECENT_LENGTH,
)
from utils.fluidsynth import FLUIDSYNTH_EXISTS
from utils.misc import incrementFilename
from utils.persistence import USE_DEFAULT
from utils.tk import blockEventFromTypes

# TODO: this file is a mess. fix it

# Program args and logging

parser = argparse.ArgumentParser(
    prog=PROGRAM_NAME,
    description="Midi tracker.",
)

fileGroup = parser.add_mutually_exclusive_group()
fileGroup.add_argument("-f", "--file", help="File to open on start.")
fileGroup.add_argument(
    "-r", "--recent", help="Open last opened file.", action="store_true"
)

loggerGroup = parser.add_mutually_exclusive_group()
loggerGroup.add_argument(
    "-d", "--debug", help="Print debug messages.", action="store_true"
)
loggerGroup.add_argument(
    "-q", "--quiet", help="Only print errors.", action="store_true"
)

wGroup = parser.add_mutually_exclusive_group()
wGroup.add_argument(
    "-w", "--windowed", help="Start in default windowed.", action="store_true"
)
wGroup.add_argument(
    "-m", "--maximized", help="Start program maximized.", action="store_true"
)

args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
elif args.quiet:
    logging.basicConfig(level=logging.CRITICAL)
else:
    logging.basicConfig(level=logging.INFO)

_logger = logging.getLogger(__name__)


# region TK Setup

root = tk.Tk()
program.p.tkRoot = root
root.option_add("*tearOff", False)
root.unbind_all("<Tab>")
root.unbind_all("<<NextWindow>>")
root.unbind_all("<<PrevWindow>>")
root.option_add("*Font", value=font.nametofont("TkFixedFont"))
root.iconphoto(True, tk.PhotoImage(file="assets/logo.png"))


def windowShape():
    def save():
        return (root.geometry(), root.state())

    def load(value):
        if args.windowed:
            root.geometry("1600x800")
        elif args.maximized:
            root.state("zoomed")
        elif value is USE_DEFAULT:
            root.state("zoomed")
        else:
            geo, state = value
            root.geometry(geo)
            root.state(state)

    program.p.persistence.register("WindowShape", save, load)


windowShape()

from interface import theme

theme.generate()

# endregion


def formatFileName(path: Path):
    return path.name


def updateWindowTitle():
    title = ""
    if program.p.currentFile is not None:
        title += formatFileName(program.p.currentFile)
        if program.p.projectModified:
            title += "* "
        title += " - "
    title += PROGRAM_NAME
    root.title(title)


updateWindowTitle()
ProjectModified.connect(updateWindowTitle)
program.p.getAttributeChangedEvent("currentFile").connect(
    lambda *_: updateWindowTitle()
)


# region Menu Setup

menubar = tk.Menu(root)
root["menu"] = menubar

recents = list[Path]()


def menus():
    def fileMenu():
        menu = tk.Menu(menubar)
        menubar.add_cascade(menu=menu, label="File")

        def promptSave(func):
            """Ask the user if they want to continue due to unsaved work. If the user selects 'cancel', the function will not be called."""

            def wrapped(*args, **kwargs):
                if program.p.projectModified:
                    result = messagebox.askyesnocancel(
                        "Unsaved Work",
                        "There is currently unsaved work, would you like to save before proceeding?",
                        icon="warning",
                    )
                    if result is None:
                        return
                    if result == True:
                        save()
                func(*args, **kwargs)

            return wrapped

        def openFile(path: Path):
            try:
                program.p.currentSong = Song.fromFile(path)
            except Exception as e:
                messagebox.showerror(
                    "File Error",
                    f"An error occurred while opening {path}:\n{traceback.format_exception_only(e)}",
                )
            else:
                program.p.currentFile = path
                program.p.projectModified = False

        @promptSave
        def open():
            filename = filedialog.askopenfilename(filetypes=PROJECT_FILE_TK_LIST)
            if filename == "" or filename == ():
                return
            openFile(Path(filename))

        # def openFile(filename)

        @promptSave
        def new():
            program.p.currentSong = Song()
            program.p.currentFile = None
            program.p.projectModified = False

        def saveAs():
            filename = filedialog.asksaveasfilename(
                filetypes=PROJECT_FILE_TK_LIST, defaultextension=PROJECT_FILE_EXTENSION
            )
            if filename == "" or filename == ():
                return
            path = Path(filename)
            try:
                program.p.currentSong.toFile(path)
            except Exception as e:
                messagebox.showerror(
                    "File Error",
                    f"An error occurred while saving:\n{traceback.format_exception_only(e)}",
                )
            else:
                program.p.projectModified = False
                program.p.currentFile = path

        def save():
            if program.p.currentFile is None:
                saveAs()
            else:
                try:
                    program.p.currentSong.toFile(program.p.currentFile)
                except Exception as e:
                    messagebox.showerror(
                        "File Error",
                        f"An error occurred while saving:\n{traceback.format_exception_only(e)}",
                    )
                else:
                    program.p.projectModified = False

        def saveIncremental():
            if program.p.currentFile is None:
                saveAs()
            else:
                program.p.currentFile = Path(
                    incrementFilename(str(program.p.currentFile))
                    + PROJECT_FILE_EXTENSION
                )
                try:
                    program.p.currentSong.toFile(program.p.currentFile)
                except Exception as e:
                    messagebox.showerror(
                        "File Error",
                        f"An error occurred while saving:\n{traceback.format_exception_only(e)}",
                    )
                else:
                    program.p.projectModified = False

        def export():
            defFilename: str | None = (
                program.p.currentFile.name.partition(".")[0]
                if program.p.currentFile is not None
                else None
            )  # Get project name from path
            if (
                program.p.currentSong.metadata.title != ""
                and not program.p.currentSong.metadata.title.isspace()
            ):
                defFilename = program.p.currentSong.metadata.title

            filename = filedialog.asksaveasfilename(
                filetypes=MIDI_FILE_TK_LIST,
                defaultextension=MIDI_FILE_EXTENSION,
                initialfile=defFilename,
            )

            if filename == "" or filename == ():
                return
            player = Player()
            player.toFile(Path(filename))

        def genRecentMenu():
            recentMenu = tk.Menu(menu)

            def loadRecents(value: list[str]):
                if value is not USE_DEFAULT:
                    # Check for missing files
                    recents.clear()
                    recents.extend(Path(dir) for dir in value)

                    if program.p.currentFile in recents:
                        recents.remove(program.p.currentFile)
                    if program.p.currentFile is not None:
                        recents.insert(0, program.p.currentFile)
                updateRecentMenu()

            def saveRecents() -> list[str]:
                return [str(r) for r in recents]

            program.p.persistence.register("Recent Files", saveRecents, loadRecents)

            def onSongChange():
                if program.p.currentFile in recents:
                    recents.remove(program.p.currentFile)
                if program.p.currentFile is not None:
                    recents.insert(0, program.p.currentFile)
                updateRecentMenu()

            program.p.getAttributeChangedEvent("currentFile").connect(
                lambda *_: onSongChange()
            )

            def openFileCommand(path):
                @promptSave
                def o():
                    openFile(path)

                return o

            def updateRecentMenu():
                recentMenu.delete(0, "end")
                for i, path in enumerate(recents):
                    if i >= RECENT_LENGTH:
                        break
                    if path.exists():
                        recentMenu.add_command(
                            label=path.name, command=openFileCommand(path)
                        )
                    else:
                        recentMenu.add_command(label=path.name, state="disabled")

            return recentMenu

        menu.add_command(label="Open", command=open)
        menu.add_cascade(label="Recent", menu=genRecentMenu())
        menu.add_command(label="New", command=new)
        menu.add_command(label="Save", command=save, accelerator="CTRL-S")
        menu.add_command(label="Save As", command=saveAs)
        menu.add_command(label="Save Incremental", command=saveIncremental)
        menu.add_command(label="Export", command=export, accelerator="CTRL-E")

        root.bind_all("<Control-S>", lambda *_: save())
        root.bind_all("<Control-E>", lambda *_: export())

        @promptSave
        def onClose():
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", onClose)

    fileMenu()

    def editMenu():
        menu = tk.Menu(menubar)
        menubar.add_cascade(menu=menu, label="Edit")

        def cut():
            focus = root.focus_get()
            if focus is not None:
                Cut.fire(focus)

        def copy():
            focus = root.focus_get()
            if focus is not None:
                Copy.fire(focus)

        def paste():
            focus = root.focus_get()
            if focus is not None:
                Paste.fire(focus)

        menu.add_command(
            label="Cut", command=cut, accelerator="CTRL-X", state="disabled"
        )
        menu.add_command(label="Copy", command=copy, accelerator="CTRL-C")
        menu.add_command(label="Paste", command=paste, accelerator="CTRL-V")

        root.bind_all("<Control-X>", lambda *_: cut())
        root.bind_all("<Control-C>", lambda *_: copy())
        root.bind_all("<Control-V>", lambda *_: paste())

    editMenu()

    def playbackMenu():
        menu = tk.Menu(menubar)
        menubar.add_cascade(menu=menu, label="Playback")

        deviceVar = tk.StringVar(root, value="No Port")

        def resetOutput():
            program.p.songPlayer.pause()  # If player is running, stop it
            p = program.p.currentPort.name
            mido.Message("reset")
            program.p.songPlayer.startLiveDaemon()  # Triggers resending internal init commands, since their
            # purpose is to modify the normal default device state

        def pausePlay():
            program.p.songPlayer.togglePlayback()

        def refresh():
            deviceMenu.delete(2, "end")
            ports = [None] + program.p.getAvailablePorts()

            for port in ports:
                if port is None:
                    display = "No Port"
                elif port.startswith(program.INTERNAL_FLUIDSYNTH_IDENTIFIER):
                    display = "Internal Fluidsynth"
                else:
                    name = port[: port.find(":")]
                    num = port[port.rfind(" ") :]
                    display = f"{name} - {num}"

                deviceMenu.add_radiobutton(
                    label=display,
                    command=createPortCommand(port),
                    variable=deviceVar,
                )

                if str(port) == str(program.p.currentPort.name):
                    deviceVar.set(str(display))

        def createPortCommand(portname: str | None):
            def command(*_):
                program.p.setPort(portname)

            return command

        menu.add_command(label="Play / Pause", command=pausePlay, accelerator="Space")
        menu.add_command(label="Reset Device", command=resetOutput)

        deviceMenu = tk.Menu(menu)
        deviceMenu.add_command(label="Refresh", command=refresh)
        deviceMenu.add_separator()
        menu.add_cascade(label="Devices", menu=deviceMenu)
        refresh()

        if FLUIDSYNTH_EXISTS:
            root.after(1000, refresh)  # Give time for Fluidsynth to boot up

            fontVar = tk.StringVar(root)

            def refreshFonts():
                fontMenu.delete(2, "end")
                # TODO: unhardcode
                for child in Path("./soundfonts").resolve().iterdir():
                    if not child.is_file():
                        return
                    if not child.name.endswith(".sf2"):
                        return
                    fontMenu.add_radiobutton(
                        label=child.name,
                        command=createFontCommand(child),
                        variable=fontVar,
                    )
                    if child == program.p.fluidsynth.lastLoadedSoundfont:
                        fontVar.set(child.name)

            def createFontCommand(path: Path):
                def command(*_):
                    program.p.fluidsynth.loadSoundfont(path)

                return command

            fontMenu = tk.Menu(menu)
            fontMenu.add_command(label="Refresh", command=refreshFonts)
            fontMenu.add_separator()
            menu.add_cascade(label="Soundfonts", menu=fontMenu)
            refreshFonts()

            # Slightly wonky, makes the auto load display properly.
            program.p.persistence.listen("soundfont", lambda value: refreshFonts())

    playbackMenu()


menus()

# endregion


def focus(event):
    try:
        event.widget.focus_set()
    except AttributeError:
        pass


root.bind_all("<Button-1>", focus)
if args.debug:
    # root.bind_all("<FocusIn>", lambda e: _logger.debug(f"FOCUS IN: {e.widget}"))
    # root.bind_all("<FocusOut>", lambda e: _logger.debug(f"FOCUS OUT: {e.widget}"))
    root.bind_all(  # Middle click identifies widget
        "<Button-2>",
        lambda e: _logger.debug(
            f"{e.widget}: {e.widget.winfo_class()}, {e.widget.winfo_name()}"
        ),
    )


# region Interface Setup

mainframe: ttk.Frame = ttk.Frame()


def layoutSetup():

    def layout1():
        if args.debug:
            ChannelDebug(mainframe).pack(side="right", fill="both")
        EffectList(mainframe).pack(side="right", fill="both")
        InstrumentList(mainframe).pack(side="right", fill="both")
        PatternViewFrame(mainframe).pack(side="bottom", fill="both", expand=True)
        PatternMatrix(mainframe).pack(side="left", fill="both")
        SongDataView(mainframe).pack(side="left", fill="both")
        PatternList(mainframe).pack(side="left", fill="both", expand=True)

    def layout2():
        side = ttk.Notebook(mainframe)
        upper = ttk.Notebook(mainframe)
        main = PatternViewFrame(mainframe)

        side.pack(side="right", fill="y")
        upper.pack(side="top", fill="x")
        main.pack(fill="both", expand=True)

        side.add(EffectList(side), text="Effects")
        side.add(InstrumentList(side), text="Instruments")
        side.add(SongDataView(side), text="Song Settings")
        if args.debug:
            side.add(ChannelDebug(side), text="Channels")

        upper.add(PatternMatrix(upper), text="Matrix")
        upper.add(PatternList(upper), text="Patterns")

    def layout3():
        right = ttk.Notebook(mainframe)
        left = ttk.Notebook(mainframe)
        main = PatternViewFrame(mainframe)

        right.pack(side="right", fill="y")
        left.pack(side="left", fill="y")
        main.pack(fill="both", expand=True)

        right.add(EffectList(right), text="Effects")
        right.add(InstrumentList(right), text="Instruments")
        if args.debug:
            right.add(ChannelDebug(right), text="Channels")

        left.add(PatternMatrix(left, width=300, controlsPos="bottom"), text="Matrix")
        left.add(SongDataView(left), text="Song Settings")
        # left.add(PatternList(left), text="Patterns")

    class UILayouts(Enum):
        Layout1 = ("Layout 1", layout1)
        Layout2 = ("Layout 2", layout2)
        Layout3 = ("Layout 3", layout3)

    currentLayout: UILayouts = UILayouts.Layout3

    def buildLayout(layout: UILayouts):
        global mainframe
        nonlocal currentLayout
        mainframe.destroy()
        mainframe = ttk.Frame(root)
        mainframe.pack(fill="both", expand=True)
        layout.value[1]()
        currentLayout = layout

    def layoutMenu():
        menu = tk.Menu(menubar)
        menubar.add_cascade(menu=menu, label="Layout")

        def c(layout: UILayouts):
            menu.add_command(label=layout.value[0], command=lambda: buildLayout(layout))

        for layout in UILayouts:
            c(layout)

    layoutMenu()

    def loadLayout(value: str):
        if value is USE_DEFAULT:
            newLayout = UILayouts.Layout3
        else:
            newLayout = UILayouts[value]
        buildLayout(newLayout)

    def saveLayout() -> str:
        return currentLayout.name

    program.p.persistence.register("Layout", saveLayout, loadLayout)


layoutSetup()

# endregion


# region Keybinds


# Global Keyboard Shortcuts
# TODO: rebindable shortcuts
def makeKeybinds():
    # I wish I could make anonymous scopes.

    # Pause/Play
    root.bind_all(
        "<space>", blockEventFromTypes(lambda *_: program.p.songPlayer.togglePlayback())
    )

    # Jump to start of pattern
    def jumpToStartOfPattern():
        program.p.songPlayer.setPlaybackCursor(None, 0)

    root.bind_all(
        "<Control-space>", blockEventFromTypes(lambda *_: jumpToStartOfPattern())
    )

    # Jump to last playback position
    def jumpToLastPlaybackPosition():
        program.p.songPlayer.setPlaybackCursor(
            program.p.songPlayer.lastMatrixRow, program.p.songPlayer.lastPatternRow
        )

    root.bind_all(
        "<Shift-space>", blockEventFromTypes(lambda *_: jumpToLastPlaybackPosition())
    )

    # Jump to start of song
    def jumpToStartOfSong():
        program.p.songPlayer.setPlaybackCursor(0, 0)

    root.bind_all(
        "<Control-Shift-space>", blockEventFromTypes(lambda *_: jumpToStartOfSong())
    )


makeKeybinds()

# endregion


# Load open files
openFile = args.file
try:
    program.p.currentSong = Song.fromFile(openFile)
    program.p.currentFile = openFile
    program.p.projectModified = False
    updateWindowTitle()
except:
    try:
        program.p.currentSong = Song.fromFile(Path("startup.tmt"))
        program.p.currentFile = None
        program.p.projectModified = False
        updateWindowTitle()
    except:
        pass


def onClose():
    program.p.persistence.save()
    program.p.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", onClose)
program.p.persistence.load()
if args.recent:
    try:
        openFile = recents[0]
        program.p.currentSong = Song.fromFile(openFile)
        program.p.currentFile = openFile
        program.p.projectModified = False
        updateWindowTitle()
    except:
        pass
root.mainloop()
