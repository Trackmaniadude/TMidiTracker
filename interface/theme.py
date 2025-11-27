import tkinter as tk
from tkinter import ttk

s = ttk.Style()
# s.theme_use("clam")

s.configure("TLabel", font="TkFixedFont")

if __name__ == "__main__":
    print(s.theme_names())
