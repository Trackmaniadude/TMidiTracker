import argparse
import logging
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import cast

from interface.program.channelDebug import ChannelDebug
from interface.program.effectList import EffectList
from interface.program.instrumentList import InstrumentList
from interface.program.patternList import PatternList
from interface.program.patternMatrix import PatternMatrix
from interface.program.patternViewFrame import PatternViewFrame
from interface.program.songDataView import SongDataView
from structures import program  # This also inits the program object
from structures.globalEvents import ProjectModified
from structures.song import Song
from utils.constants import PROJECT_FILE

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

args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
elif args.quiet:
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

_logger = logging.getLogger(__name__)


# Setup TK

root = tk.Tk()
root.state("zoomed")
# root.geometry("800x600")
root.option_add("*tearOff", False)
root.unbind_all("<Tab>")
root.unbind_all("<<NextWindow>>")
root.unbind_all("<<PrevWindow>>")

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
            filename = filedialog.askopenfilename(filetypes=PROJECT_FILE)
            if filename == "":
                return
            try:
                program.p.currentSong = Song.fromFile(filename)
            except:
                pass
                # TODO: tell user
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
            filename = filedialog.asksaveasfilename(filetypes=PROJECT_FILE)
            if filename == "":
                return
            try:
                program.p.currentSong.toFile(filename)
            except:
                pass
            else:
                program.p.projectModified = False
                program.p.currentFile = filename

        def save():
            if program.p.currentFile is None:
                saveAs()
            else:
                try:
                    program.p.currentSong.toFile(program.p.currentFile)
                except:
                    pass
                else:
                    program.p.projectModified = False

        menu.add_command(label="Open", command=open)
        menu.add_command(label="New", command=new)
        menu.add_command(label="Save", command=save, accelerator="CTRL-S")
        menu.add_command(label="Save As", command=saveAs)

        root.bind_all("<Control-S>", lambda *_: save())

        def onClose():
            if promptSaveFirst():
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", onClose)

    fileMenu()


menus()


def focus(event):
    try:
        event.widget.focus_set()
    except AttributeError:
        pass


root.bind_all("<Button-1>", focus)
if args.debug:
    root.bind_all("<FocusIn>", lambda e: _logger.debug(f"FOCUS IN: {e.widget}"))
    root.bind_all("<FocusOut>", lambda e: _logger.debug(f"FOCUS OUT: {e.widget}"))
    root.bind_all(
        "<Button-2>",
        lambda e: _logger.debug(
            f"{e.widget}: {e.widget.winfo_class()}, {e.widget.winfo_name()}"
        ),
    )


# Setup interface

if args.debug:
    ChannelDebug(root).pack(side="right", fill="both")
EffectList(root).pack(side="right", fill="both")
InstrumentList(root).pack(side="right", fill="both")
PatternViewFrame(root).pack(side="bottom", fill="both", expand=True)
PatternMatrix(root).pack(side="left", fill="both")
SongDataView(root).pack(side="left", fill="both")
PatternList(root).pack(side="left", fill="both", expand=True)


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
# openFile = args.file
# try:
#     program.p.currentSong = Song.fromFile(openFile)
# except:
#     try:
#         program.p.currentSong = Song.fromFile("startup.tmt")
#     except:
#         pass


root.mainloop()
program.p.close()
