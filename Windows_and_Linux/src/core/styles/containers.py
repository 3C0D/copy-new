"""
Container styles for Writing Tools UI components.
Includes dialogs, containers, and layout elements.
"""

from .colors import ColorPalette


def dialog(palette: ColorPalette) -> str:
    """Dialog window style."""
    return f"""
        QDialog {{
            background-color: {palette.bg_primary};
            color: {palette.fg_primary};
        }}
    """


def container(palette: ColorPalette) -> str:
    """Generic container style."""
    return f"""
        QWidget {{
            background-color: transparent;
            border: 1px solid {"#666666" if palette.bg_primary == "#2d2d2d" else "#777777D2"};
            border-radius: 8px;
            padding: 8px;
        }}
    """


def image_preview(palette: ColorPalette) -> str:
    """Image preview container style."""
    return f"""
        QLabel {{
            border: 1px solid {"rgba(0, 140, 186, 0.8)" if palette.bg_primary == "#ffffff" else "rgba(76, 175, 80, 0.8)"};
            border-radius: 4px;
            {"background-color: rgba(248, 248, 248, 0.4);" if palette.bg_primary == "#ffffff" else "background-color: rgba(255, 255, 255, 0.1);"}
        }}
    """


def non_editable_modal(palette: ColorPalette) -> str:
    """Non-editable modal dialog style."""
    return f"""
        QWidget {{
            background-color: {"#2a2a2a" if palette.bg_primary == "#2d2d2d" else "#ffffff"};
            border: 1px solid {"#404040" if palette.bg_primary == "#2d2d2d" else "#d0d0d0"};
            border-radius: 8px;
        }}
        QTextBrowser {{
            background-color: {"#1e1e1e" if palette.bg_primary == "#2d2d2d" else "#f5f5f5"};
            color: {"#ffffff" if palette.bg_primary == "#2d2d2d" else "#000000"};
            border: 1px solid {"#404040" if palette.bg_primary == "#2d2d2d" else "#d0d0d0"};
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton {{
            background-color: {"#404040" if palette.bg_primary == "#2d2d2d" else "#e8e8e8"};
            border: none;
            border-radius: 4px;
            color: {"#ffffff" if palette.bg_primary == "#2d2d2d" else "#000000"};
            font-size: 16px;
        }}
        QPushButton:hover {{
            background-color: #4a9eff;
            {"" if palette.bg_primary == "#2d2d2d" else "color: #ffffff;"}
        }}
    """
