import os
from pathlib import Path

# Path to the forge.exe binary, relative to the package root
FORGE_BIN_PATH = Path(__file__).parent.parent / 'sandbox' / 'forge' / 'forge.exe'

# Default deck directory, relative to the package root
DEFAULT_DECK_DIR = Path(__file__).parent.parent / 'decks'
