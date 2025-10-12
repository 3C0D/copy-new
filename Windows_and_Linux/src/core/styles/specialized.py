"""
Specialized styles for Writing Tools UI components.
Includes markdown rendering, response windows, and custom components.
"""

from .colors import ColorPalette


def markdown_text_browser_ai(palette: ColorPalette) -> str:
    """Markdown text browser for AI messages."""
    return f"""
        QTextBrowser {{
            background-color: {"#333" if palette.bg_primary == "#2d2d2d" else "#f8f9fa"};
            color: {"#ffffff" if palette.bg_primary == "#2d2d2d" else "#212529"};
            border: 1px solid {"#555" if palette.bg_primary == "#2d2d2d" else "#dee2e6"};
            border-radius: 8px;
            padding: 8px;
            margin: 0px;
            line-height: 1.3;
            width: 100%;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }}
        th, td {{
            border: 1px solid {"#555" if palette.bg_primary == "#2d2d2d" else "#dee2e6"};
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: {"#444" if palette.bg_primary == "#2d2d2d" else "#e9ecef"};
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: {"#3a3a3a" if palette.bg_primary == "#2d2d2d" else "#f8f9fa"};
        }}
        tr:hover {{
            background-color: {"#484848" if palette.bg_primary == "#2d2d2d" else "#e9ecef"};
        }}
    """


def markdown_text_browser_user(palette: ColorPalette) -> str:
    """Markdown text browser for user messages."""
    return f"""
        QTextBrowser {{
            background-color: transparent;
            color: {"#ffffff" if palette.bg_primary == "#2d2d2d" else "#212529"};
            border: none;
            border-radius: 8px;
            padding: 8px;
            margin: 0px;
            line-height: 1.3;
            width: 100%;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }}
        th, td {{
            border: 1px solid {"#555" if palette.bg_primary == "#2d2d2d" else "#dee2e6"};
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: {"#444" if palette.bg_primary == "#2d2d2d" else "#e9ecef"};
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: {"#3a3a3a" if palette.bg_primary == "#2d2d2d" else "#f8f9fa"};
        }}
        tr:hover {{
            background-color: {"#484848" if palette.bg_primary == "#2d2d2d" else "#e9ecef"};
        }}
    """


def icon_button(palette: ColorPalette) -> str:
    """Icon button style."""
    return f"""
        QPushButton {{
            background-color: {"#666" if palette.bg_primary == "#2d2d2d" else "#999"};
            border-radius: 10px;
            min-width: 16px;
            min-height: 16px;
            max-width: 16px;
            max-height: 16px;
            padding: 1px;
            margin: 0px;
        }}
        QPushButton:hover {{
            background-color: {"#888" if palette.bg_primary == "#2d2d2d" else "#bbb"};
        }}
    """
