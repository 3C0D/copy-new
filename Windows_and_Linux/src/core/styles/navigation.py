"""
Navigation styles for Writing Tools UI components.
Includes scrollbars, menus, and navigation elements.
"""

from .colors import ColorPalette


def chat_scroll_area(palette: ColorPalette) -> str:
    """Chat scroll area style."""
    return f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background-color: {"rgba(0, 0, 0, 0.1)" if palette.bg_primary == "#ffffff" else "rgba(255, 255, 255, 0.1)"};
            width: 12px;
            margin: 0px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {"rgba(128, 128, 128, 0.6)" if palette.bg_primary == "#ffffff" else "rgba(200, 200, 200, 0.6)"};
            min-height: 20px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {"rgba(128, 128, 128, 0.8)" if palette.bg_primary == "#ffffff" else "rgba(220, 220, 220, 0.8)"};
        }}
        QScrollBar::handle:vertical:pressed {{
            background-color: {"rgba(128, 128, 128, 1.0)" if palette.bg_primary == "#ffffff" else "rgba(240, 240, 240, 1.0)"};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
    """


def tray_menu(palette: ColorPalette) -> str:
    """System tray menu style."""
    return f"""
        QMenu {{
            background-color: {palette.bg_primary};
            color: {palette.fg_primary};
            border: 1px solid {palette.border};
            border-radius: 8px;
            padding: 2px;
            selection-background-color: {palette.selection};
        }}
        QMenu::item {{
            padding: 4px 20px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {palette.selection};
        }}
    """
