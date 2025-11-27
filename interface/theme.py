import tkinter as tk
from tkinter import ttk

NOTE_BG = "#FFFFFF"
NOTE_MINOR = "#EEEEEE"
NOTE_MAJOR = "#CCCCCC"

NOTE_BG_TARGET = "#EEEEEE"
NOTE_MINOR_TARGET = "#DDDDDD"
NOTE_MAJOR_TARGET = "#BBBBBB"

s = ttk.Style()
# s.theme_use("clam")

s.configure("TLabel", font="TkFixedFont")
s.configure("TButton", font="TkFixedFont")
s.configure("TEntry", font="TkFixedFont")

s.configure("Note.TLabel", font="TkFixedFont", background=NOTE_BG)
s.configure("NoteMinor.TLabel", font="TkFixedFont", background=NOTE_MINOR)
s.configure("NoteMajor.TLabel", font="TkFixedFont", background=NOTE_MAJOR)
s.configure("NoteTarget.TLabel", font="TkFixedFont", background=NOTE_BG_TARGET)
s.configure("NoteMinorTarget.TLabel", font="TkFixedFont", background=NOTE_MINOR_TARGET)
s.configure("NoteMajorTarget.TLabel", font="TkFixedFont", background=NOTE_MAJOR_TARGET)

if __name__ == "__main__":
    print(s.theme_names())
