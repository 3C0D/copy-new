"""
Feedback styles for Writing Tools UI components.
Includes progress bars, tooltips, and status indicators.
"""

from .colors import ColorPalette


def progress_window(palette: ColorPalette) -> str:
    """Progress window style."""
    return f"""
        QDialog {{
            background-color: {"#2b2b2b" if palette.bg_primary == "#2d2d2d" else "#ffffff"};
            color: {"#ffffff" if palette.bg_primary == "#2d2d2d" else "#333333"};
        }}
        QLabel {{
            font-size: 14px;
            color: {"#ffffff" if palette.bg_primary == "#2d2d2d" else "#333333"};
        }}
        QPushButton {{
            background-color: {palette.primary_default};
            color: white;
            padding: 8px 16px;
            font-size: 12px;
            border: none;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {palette.primary_hover};
        }}
        QProgressBar {{
            background-color: {"#444444" if palette.bg_primary == "#2d2d2d" else "#f0f0f0"};
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {palette.primary_default};
            border-radius: 3px;
        }}
    """
