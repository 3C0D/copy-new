from PySide6.QtWidgets import QApplication


class ClipboardManager:
    """Manages clipboard operations."""

    def __init__(self, app, logger):
        self._logger = logger
        self.app = app

    def backup_clipboard(self) -> str:
        """Backup current clipboard content."""
        clipboard = QApplication.clipboard()
        return clipboard.text() if clipboard else ""

    def restore_clipboard(self, content: str) -> None:
        """Restore clipboard to previous content."""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(content)

    def clear_clipboard(self) -> None:
        """Clear clipboard content."""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.clear()

    def _clear_clipboard_safely(self, success: bool = True) -> None:
        """
        Clear clipboard only if operation was successful.

        Args:
            success: Whether the previous operation was successful
        """
        if not success:
            return

        try:
            self.app.clipboard_manager.clear_clipboard()
            self._logger.debug("Clipboard cleared after successful operation")
        except Exception as e:
            self._logger.warning(f"Failed to clear clipboard: {e}")
