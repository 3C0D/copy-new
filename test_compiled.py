#!/usr/bin/env python3
"""
Test script to check if running from compiled exe
"""

import sys
import os
from pathlib import Path

def is_compiled():
    return hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS")

def get_startup_path():
    if not is_compiled():
        return None
    return sys.executable

print("is_compiled():", is_compiled())
print("sys.executable:", sys.executable)
print("get_startup_path():", get_startup_path())
print("sys.frozen:", hasattr(sys, "frozen"))
print("sys._MEIPASS:", hasattr(sys, "_MEIPASS"))

if hasattr(sys, "_MEIPASS"):
    print("_MEIPASS:", sys._MEIPASS)