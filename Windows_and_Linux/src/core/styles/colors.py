"""
Color palettes and theme definitions for Writing Tools.
Centralized color management for consistent theming across the application.
"""

from dataclasses import dataclass


@dataclass
class ColorPalette:
    """Complete color palette for a theme (dark or light)."""

    # Background colors
    bg_primary: str
    bg_secondary: str
    bg_control: str

    # Foreground/Text colors
    fg_primary: str
    fg_secondary: str
    fg_control: str
    fg_control_text: str

    # Borders and accents
    border: str
    border_checkbox: str
    selection: str

    # Button colors
    primary_default: str
    primary_hover: str
    primary_pressed: str

    secondary_default: str
    secondary_hover: str
    secondary_pressed: str

    # Special states
    close_default: str
    close_hover: str
    close_pressed: str

    # Additional colors
    delete_default: str = "#dc3545"
    delete_hover: str = "#c82333"
    delete_pressed: str = "#bd2130"


# Dark theme palette
DARK_PALETTE = ColorPalette(
    # Backgrounds
    bg_primary="#2d2d2d",
    bg_secondary="#3a3a3a",
    bg_control="#444444",

    # Text
    fg_primary="#ffffff",
    fg_secondary="#cccccc",
    fg_control="#ffffff",
    fg_control_text="#ffffff",

    # Borders and accents
    border="#666666",
    border_checkbox="#666666",
    selection="#666",

    # Buttons
    primary_default="#4CAF50",
    primary_hover="#45a049",
    primary_pressed="#3d8b40",

    secondary_default="#666666",
    secondary_hover="#555555",
    secondary_pressed="#444444",

    # Special states
    close_default="#3d8b40",
    close_hover="#2e7d32",
    close_pressed="#1b5e20",
)

# Light theme palette
LIGHT_PALETTE = ColorPalette(
    # Backgrounds
    bg_primary="#ffffff",
    bg_secondary="#f8f9fa",
    bg_control="white",

    # Text
    fg_primary="#000000",
    fg_secondary="#333333",
    fg_control="#000000",
    fg_control_text="#333333",

    # Borders and accents
    border="#cccccc",
    border_checkbox="#cccccc",
    selection="#e0e0e0",

    # Buttons
    primary_default="#008CBA",
    primary_hover="#007095",
    primary_pressed="#005f7a",

    secondary_default="#cccccc",
    secondary_hover="#bbbbbb",
    secondary_pressed="#aaaaaa",

    # Special states
    close_default="#0277bd",
    close_hover="#01579b",
    close_pressed="#004d40",
)