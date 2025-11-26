if not exist ".venv\" (
    python -m venv .venv
)
call .venv/scripts/activate
if not exist "INSTALLED" (
    pip install -r requirements.txt
    type nul > "INSTALLED"
)
python main.py %*