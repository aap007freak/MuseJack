import os
import sys
from pathlib import Path


def load_musescore_ini(path: Path) -> dict:
    out = dict()
    with open(path) as musescore_ini_file:
        for line in musescore_ini_file:
            if not line.startswith("[") and line.strip():
                parts = line.strip().split("=", maxsplit=1)
                out[parts[0]] = parts[1]

    return out


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS,  relative_path) # executable with pyinstaller
    return os.path.join(os.path.abspath("../resources"), relative_path) # executing using python

