"""
Control styles for Writing Tools UI components.
Includes buttons, inputs, dropdowns, and other interactive controls.
"""

from .colors import ColorPalette


def neutral_button(palette: ColorPalette) -> str:
    """Neutral/default button style for action buttons - uses subtle colors."""
    return f"""
        QPushButton {{
            font-size: 14px;
            padding: 8px 16px;
            border: 1px solid {palette.border};
            background-color: {palette.bg_control};
            color: {palette.fg_control};
        }}
        QPushButton:hover {{
            background-color: {palette.selection};
        }}
        QPushButton:pressed {{
            background-color: {palette.border};
        }}
    """


def primary_button(palette: ColorPalette) -> str:
    """Primary action button style."""
    return f"""
        QPushButton {{
            background-color: {palette.primary_default};
            border: none;
            color: white;
            padding: 10px;
            font-size: 16px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {palette.primary_hover};
        }}
        QPushButton:pressed {{
            background-color: {palette.primary_pressed};
        }}
        QPushButton:disabled {{
            background-color: {palette.primary_pressed};
            color: #bdbdbd;
            border-color: {palette.primary_pressed};
        }}
    """


def secondary_button(palette: ColorPalette) -> str:
    """Secondary action button style."""
    return f"""
        QPushButton {{
            background-color: {palette.secondary_default};
            color: {palette.fg_primary if palette == palette else "#333333"};
            padding: 8px 12px;
            font-size: 14px;
            border: none;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {palette.secondary_hover};
        }}
        QPushButton:pressed {{
            background-color: {palette.secondary_pressed};
        }}
    """


def close_button(palette: ColorPalette) -> str:
    """Close/exit button style."""
    return f"""
        QPushButton {{
            background-color: {palette.close_default};
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
            padding: 8px 16px;
        }}
        QPushButton:hover {{
            background-color: {palette.close_hover};
        }}
        QPushButton:pressed {{
            background-color: {palette.close_pressed};
        }}
    """


def delete_button(palette: ColorPalette) -> str:
    """Delete/remove button style."""
    return f"""
        QPushButton {{
            background-color: {palette.delete_default};
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 14px;
            font-weight: bold;
            min-width: 20px;
            min-height: 20px;
            padding: 0;
        }}
        QPushButton:hover {{
            background-color: {palette.delete_hover};
        }}
        QPushButton:pressed {{
            background-color: {palette.delete_pressed};
        }}
    """


def input_field(palette: ColorPalette) -> str:
    """Text input field style."""
    return f"""
        QLineEdit {{
            font-size: 16px;
            padding: 5px;
            background-color: {palette.bg_control};
            color: {palette.fg_control};
            border: 1px solid {palette.border};
        }}
    """


def dropdown(palette: ColorPalette) -> str:
    """Dropdown/combobox style."""
    return f"""
        QComboBox {{
            background-color: {palette.bg_control};
            color: {palette.fg_control};
            border: 1px solid {palette.border};
            padding: 5px;
            font-size: 16px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {palette.bg_control};
            color: {palette.fg_control};
            selection-background-color: {palette.selection};
        }}
    """


def radio_button(palette: ColorPalette) -> str:
    """Radio button style."""
    return f"""
        QRadioButton {{
            color: {palette.fg_control_text};
            font-size: 16px;
        }}
    """


def checkbox(palette: ColorPalette) -> str:
    """Checkbox style."""
    return f"""
        QCheckBox {{
            color: {palette.fg_control_text};
            font-size: 16px;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 13px;
            height: 13px;
            border-radius: 2px;
        }}
        QCheckBox::indicator:unchecked {{
            border: 2px solid {palette.border_checkbox};
            background-color: {palette.bg_control};
        }}
        QCheckBox::indicator:checked {{
            border: 2px solid {palette.border_checkbox};
            background-color: {palette.border_checkbox};
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iOSIgaGVpZ2h0PSI5IiB2aWV3Qm94PSIwIDAgOSA5IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cGF0aCBkPSJNNy41IDIuNUwzLjc1IDYuMjVMMi41IDUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS4yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==);
        }}
    """


def icon_small_button(palette: ColorPalette) -> str:
    """Small icon button style."""
    return f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 0px;
            margin-top: 3px;
            color: {palette.fg_control};
        }}
        QPushButton:hover {{
            background-color: {palette.selection};
        }}
    """


def close_small_button(palette: ColorPalette) -> str:
    """Small close button style."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {palette.fg_control};
            font-size: 20px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {palette.selection};
        }}
    """


def add_button(palette: ColorPalette) -> str:
    """Add new item button style."""
    return f"""
        QPushButton {{
            background-color: {palette.bg_control if palette.bg_primary == "#2d2d2d" else "#e0e0e0"};
            border: 1px solid {palette.border};
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
            text-align: center;
            color: {palette.fg_control};
            margin-top: 10px;
        }}
        QPushButton:hover {{
            background-color: {palette.selection if palette.bg_primary == "#2d2d2d" else "#d0d0d0"};
        }}
    """


def lock_button(palette: ColorPalette) -> str:
    """Lock/unlock toggle button style."""
    return f"""
        QPushButton {{
            {"background-color: #f0f0f0; color: #333333;" if palette.bg_primary == "#ffffff" else f"background-color: {palette.secondary_default}; color: {palette.fg_primary};"}
            border: 1px solid {"#999999" if palette.bg_primary == "#ffffff" else palette.border};
            border-radius: 4px;
            padding: 2px;
            font-size: 14px;
            min-width: 20px;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {palette.selection};
            border: 1px solid {"#777777" if palette.bg_primary == "#ffffff" else "#888888"};
        }}
        QPushButton:checked {{
            background-color: #4CAF50;
            color: white;
            border: 1px solid #4CAF50;
        }}
    """


def input_full(palette: ColorPalette) -> str:
    """Full-width input field with focus effects."""
    return f"""
        QLineEdit {{
            padding: 10px;
            border: 2px solid {palette.border};
            border-radius: 8px;
            background-color: {palette.bg_control};
            color: {palette.fg_control};
            font-size: 14px;
        }}
        QLineEdit:focus {{
            border-color: {"#4CAF50" if palette.bg_primary == "#2d2d2d" else "#2196F3"};
        }}
    """


def send_button(palette: ColorPalette) -> str:
    """Send/submit button style."""
    return f"""
        QPushButton {{
            background-color: {"#2e7d32" if palette.bg_primary == "#2d2d2d" else "#4CAF50"};
            border: none;
            border-radius: 8px;
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: {"#1b5e20" if palette.bg_primary == "#2d2d2d" else "#45a049"};
        }}
    """


def copy_button(palette: ColorPalette) -> str:
    """Copy button style - subtle and theme-appropriate."""
    return f"""
        QToolButton {{
            background-color: {palette.bg_control};
            border: 1px solid {palette.border};
            border-radius: 6px;
            padding: 2px;
            color: {palette.fg_control};
        }}
        QToolButton:hover {{
            background-color: {palette.selection};
            border: 1px solid {palette.border};
        }}
    """


def copy_button_success(palette: ColorPalette) -> str:
    """Copy button success feedback style."""
    return f"""
        QToolButton {{
            background-color: rgba(76, 175, 80, 0.9);
            border: 1px solid #4CAF50;
            border-radius: 6px;
            padding: 2px;
        }}
    """