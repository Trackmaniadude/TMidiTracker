#!/bin/bash
if ! [ -d ".venv" ]; then
   python3 -m venv .venv
fi
source .venv/bin/activate
if ! [ -f "INSTALLED" ]; then
   pip install -r requirements.txt
   touch INSTALLED
fi
python3 main.py "$@"