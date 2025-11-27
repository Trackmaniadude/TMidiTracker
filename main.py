import argparse
import logging
import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import cast

from interface.program.patternViewFrame import PatternViewFrame
from structures import program

PROGRAM_NAME = "TMidiTracker"

parser = argparse.ArgumentParser(
    prog=PROGRAM_NAME,
    description="Midi tracker.",
)

# parser.add_argument("-f", "--file", help="File to open on start.")

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


root = tk.Tk()
root.title(PROGRAM_NAME)
root.state("zoomed")
# root.geometry("800x600")
root.option_add("*tearOff", False)

PatternViewFrame(root).pack(fill="both", expand=True)


root.mainloop()
