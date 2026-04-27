import argparse
import logging
import tkinter as tk
import traceback
from enum import Enum
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
from utils import persistence
from utils.constants import (
    CHANNEL_COUNT,
    MIDI_FILE_EXTENSION,
    MIDI_FILE_TK_LIST,
    PROJECT_FILE_EXTENSION,
    PROJECT_FILE_TK_LIST,
)
from utils.misc import incrementFilename

PROGRAM_NAME = "TMidiTracker"

# Program args and logging

parser = argparse.ArgumentParser(
    prog=PROGRAM_NAME,
    description="Midi tracker.",
)

parser.add_argument("-f", "--file", help="File to open on start.")

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


# Setup TK

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
        elif value is persistence.USE_DEFAULT:
            root.state("zoomed")
        else:
            geo, state = value
            root.geometry(geo)
            root.state(state)

    persistence.registerPersistence("WindowShape", save, load)


windowShape()

from interface import theme

theme.generate()


def formatFileName(fn: str):
    return fn


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


# Setup menus

menubar = tk.Menu(root)
root["menu"] = menubar


def menus():
    def fileMenu():
        menu = tk.Menu(menubar)
        menubar.add_cascade(menu=menu, label="File")

        def promptSaveFirst() -> bool:
            """Ask the user if they want to continue due to unsaved work. Returns true if we may continue (user did not select 'cancel')"""
            # TODO: should this also return false if the user says "yes" but then cancels the save?
            if not program.p.projectModified:
                return True
            result = messagebox.askyesnocancel(
                "Unsaved Work",
                "There is currently unsaved work, would you like to save before proceeding?",
                icon="warning",
            )
            if result == True:
                save()
            if result is None:
                return False
            return True

        def open():
            if not promptSaveFirst():
                return
            filename = filedialog.askopenfilename(filetypes=PROJECT_FILE_TK_LIST)
            if filename == "":
                return
            try:
                program.p.currentSong = Song.fromFile(filename)
            except Exception as e:
                messagebox.showerror(
                    "File Error",
                    f"An error occurred while opening {filename}:\n{traceback.format_exception_only(e)}",
                )
            else:
                program.p.currentFile = filename
                program.p.projectModified = False

        def new():
            if not promptSaveFirst():
                return
            program.p.currentSong = Song()
            program.p.currentFile = None
            program.p.projectModified = False

        def saveAs():
            filename = filedialog.asksaveasfilename(
                filetypes=PROJECT_FILE_TK_LIST, defaultextension=PROJECT_FILE_EXTENSION
            )
            if filename == "":
                return
            try:
                program.p.currentSong.toFile(filename)
            except Exception as e:
                messagebox.showerror(
                    "File Error",
                    f"An error occurred while saving:\n{traceback.format_exception_only(e)}",
                )
            else:
                program.p.projectModified = False
                program.p.currentFile = filename

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
                program.p.currentFile = (
                    incrementFilename(
                        program.p.currentFile[: program.p.currentFile.rfind(".")]
                    )
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
            filename = filedialog.asksaveasfilename(
                filetypes=MIDI_FILE_TK_LIST, defaultextension=MIDI_FILE_EXTENSION
            )
            if filename == "":
                return
            player = Player()
            player.toFile(filename)

        menu.add_command(label="Open", command=open)
        menu.add_command(label="New", command=new)
        menu.add_command(label="Save", command=save, accelerator="CTRL-S")
        menu.add_command(label="Save As", command=saveAs)
        menu.add_command(label="Save Incremental", command=saveIncremental)
        menu.add_command(label="Export", command=export, accelerator="CTRL-E")

        root.bind_all("<Control-S>", lambda *_: save())
        root.bind_all("<Control-E>", lambda *_: export())

        def onClose():
            if promptSaveFirst():
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

        menu.add_command(label="Cut", command=cut, accelerator="CTRL-X")
        menu.add_command(label="Copy", command=copy, accelerator="CTRL-C")
        menu.add_command(label="Paste", command=paste, accelerator="CTRL-V")

        root.bind_all("<Control-X>", lambda *_: cut())
        root.bind_all("<Control-C>", lambda *_: copy())
        root.bind_all("<Control-V>", lambda *_: paste())

    editMenu()

    def portMenu():
        menu = tk.Menu(menubar)
        menubar.add_cascade(menu=menu, label="Playback")

        def resetOutput():
            program.p.songPlayer.pause()  # If player is running, stop it
            p = program.p.currentPort.name
            program.p.setPort(None)
            program.p.setPort(p)
            for channel in range(CHANNEL_COUNT):
                program.p.currentPort.send(
                    mido.Message(
                        "control_change", channel=channel, control=120, value=0
                    )
                )
                program.p.currentPort.send(
                    mido.Message(
                        "control_change", channel=channel, control=121, value=0
                    )
                )
            program.p.songPlayer.startLiveDaemon()  # Triggers resending internal init commands, since their
            # purpose is to modify the normal default device state

        def pausePlay():
            program.p.songPlayer.togglePlayback()

        def refresh():
            menu.delete(5, "end")
            ports = [None] + program.p.getAvailablePorts()
            for port in ports:
                menu.add_radiobutton(
                    label=port if port is not None else "No Port",
                    command=createPortCommand(port),
                )

        def createPortCommand(portname: str | None):
            def command(*_):
                program.p.setPort(portname)

            return command

        menu.add_command(label="Pause/Play", command=pausePlay, accelerator="Space")
        menu.add_command(label="Reset Output", command=resetOutput)
        menu.add_separator()
        menu.add_command(label="Refresh", command=refresh)
        menu.add_separator()
        refresh()

    portMenu()


menus()


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


# Setup interface

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
        if value is persistence.USE_DEFAULT:
            newLayout = UILayouts.Layout3
        else:
            newLayout = UILayouts[value]
        buildLayout(newLayout)

    def saveLayout() -> str:
        return currentLayout.name

    persistence.registerPersistence("Layout", saveLayout, loadLayout)


layoutSetup()


# Global Keyboard Shortcuts
# TODO: rebindable shortcuts
def makeKeybinds():
    # I wish I could make anonymous scopes.

    # Pause/Play
    root.bind_all("<space>", lambda *_: program.p.songPlayer.togglePlayback())

    # Jump to start of pattern
    def jumpToStartOfPattern():
        program.p.songPlayer.setPlaybackCursor(None, 0)

    root.bind_all("<Control-space>", lambda *_: jumpToStartOfPattern())

    # Jump to last playback position
    def jumpToLastPlaybackPosition():
        program.p.songPlayer.setPlaybackCursor(
            program.p.songPlayer.lastMatrixRow, program.p.songPlayer.lastPatternRow
        )

    root.bind_all("<Shift-space>", lambda *_: jumpToLastPlaybackPosition())

    # Jump to start of song
    def jumpToStartOfSong():
        program.p.songPlayer.setPlaybackCursor(0, 0)

    root.bind_all("<Control-Shift-space>", lambda *_: jumpToStartOfSong())


makeKeybinds()


# Load open files
openFile = args.file
try:
    program.p.currentSong = Song.fromFile(openFile)
    program.p.currentFile = openFile
    program.p.projectModified = False
    updateWindowTitle()
except:
    try:
        program.p.currentSong = Song.fromFile("startup.tmt")
        program.p.currentFile = None
        program.p.projectModified = False
        updateWindowTitle()
    except:
        pass


def onClose():
    persistence.savePersistence()
    program.p.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", onClose)
persistence.loadPersistence()
root.mainloop()
