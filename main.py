import argparse
import logging
import os
import tkinter as tk
import traceback
from tkinter import filedialog, font, messagebox, ttk
from typing import cast

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
    MIDI_FILE_EXTENSION,
    MIDI_FILE_TK_LIST,
    PROJECT_FILE_EXTENSION,
    PROJECT_FILE_TK_LIST,
)

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

parser.add_argument("-w", "--windowed", help="Start in windowed.", action="store_true")

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
program.p.tkRoot = root
if args.windowed:
    root.geometry("1600x800")
else:
    root.state("zoomed")
root.option_add("*tearOff", False)
root.unbind_all("<Tab>")
root.unbind_all("<<NextWindow>>")
root.unbind_all("<<PrevWindow>>")
root.option_add("*Font", value=font.nametofont("TkFixedFont"))
root.iconphoto(True, tk.PhotoImage(file="assets/logo.png"))

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

        def restartPlayer():
            program.p.songPlayer.startLiveDaemon()

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
        menu.add_command(label="Restart Playback Thread", command=restartPlayer)
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


root.mainloop()
program.p.close()
