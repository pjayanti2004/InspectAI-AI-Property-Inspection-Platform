"""sitecustomize — ensures project root is on sys.path for all Streamlit pages.

Streamlit runs pages/*.py as independent modules. The sys.path fix in app.py
does not apply to page modules loaded before app.py executes. This file is
automatically imported by Python on startup (via the site module), making the
project root available for absolute imports like `from streamlit_app.X import Y`.
"""
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
