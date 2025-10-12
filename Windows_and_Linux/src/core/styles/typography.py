"""
Typography styles for Writing Tools UI components.
Includes labels, text elements, and font styling.
"""

from .colors import ColorPalette


def label(palette: ColorPalette) -> str:
    """Standard label style."""
    return f"""
        QLabel {{
            font-size: 16px;
            color: {palette.fg_control_text};
        }}
    """


def label_small(palette: ColorPalette) -> str:
    """Small label style."""
    return f"""
        QLabel {{
            font-size: 14px;
            color: {palette.fg_control_text};
        }}
    """


def label_title(palette: ColorPalette) -> str:
    """Title label style."""
    return f"""
        QLabel {{
            font-size: 24px;
            font-weight: bold;
            color: {palette.fg_primary};
        }}
    """


def warning_label(palette: ColorPalette) -> str:
    """Warning/error label style."""
    return """
        QLabel {
            font-size: 14px;
            color: #ff6b6b;
            font-weight: bold;
        }
    """


def action_indicator(palette: ColorPalette) -> str:
    """Action indicator label style."""
    return f"""
        QLabel {{
            background-color: {palette.secondary_default};
            color: {palette.fg_primary};
            border-radius: 10px;
            font-size: 12px;
            font-weight: bold;
            padding: 2px;
            min-width: 16px;
            max-width: 16px;
            min-height: 16px;
            max-height: 16px;
            text-align: center;
        }}
    """
