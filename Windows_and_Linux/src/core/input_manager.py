import time

from pynput import keyboard


class InputManager:
    """Manages input operations like text selection and keyboard simulation."""

    def __init__(self, app, logger):
        self.app = app
        self._logger = logger

    def get_selected_text(
        self, sleep_duration: float = 0.2, max_retries: int = 3, retry_delay: float = 0.1
    ) -> str:
        """
        Get the currently selected text from any application by simulating Ctrl+C.
        """
        self._logger.debug("Getting selected text")
        clipboard_backup = self.app.clipboard_manager.backup_clipboard()
        self._logger.debug(
            f"Clipboard backed up: {clipboard_backup[:30] if clipboard_backup else 'Empty'} ..."
        )

        # Clear the clipboard
        self.app.clipboard_manager.clear_clipboard()
        selected_text = ""

        # Simulate Ctrl+C to copy selected text
        self._logger.debug("Simulating Ctrl+C")

        # Retry mechanism for Ctrl+C
        for attempt in range(max_retries):
            self._logger.debug(f"Attempting Ctrl+C - attempt {attempt + 1}/{max_retries}")

            # Clear clipboard before each attempt to detect success
            self.app.clipboard_manager.clear_clipboard()

            # Simulate Ctrl+C
            self.simulate_ctrl_key("c")

            # Wait for clipboard to update
            time.sleep(sleep_duration)

            # Check if clipboard has new content
            current_clipboard = self.app.clipboard_manager.backup_clipboard()

            if current_clipboard:  # Success - clipboard has content
                # Check if it's a file path (from QuickLook/file selection)
                if self._is_file_path(current_clipboard):
                    self._logger.debug(
                        f"Detected file path, treating as no selection: {current_clipboard}"
                    )
                    selected_text = ""
                    break
                else:
                    selected_text = current_clipboard
                    self._logger.debug(
                        f"Ctrl+C successful on attempt {attempt + 1}: {selected_text[:30] if selected_text else 'Empty'} ..."
                    )
                    break
            else:
                # Failed attempt
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    self._logger.debug(
                        f"Ctrl+C failed on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                else:
                    self._logger.warning(
                        f"Ctrl+C failed after {max_retries} attempts - no text selected or clipboard access failed"
                    )

        # Clean the selected text
        if selected_text:
            self._logger.debug(f"Text retrieved and cleaned: {len(selected_text)} characters")
        else:
            selected_text = ""
            self._logger.debug("No text was retrieved")

        # Restore the clipboard
        self.app.clipboard_manager.restore_clipboard(clipboard_backup if clipboard_backup else "")
        self._logger.debug("Clipboard restored")

        return selected_text

    def simulate_ctrl_key(self, key: str) -> None:
        """Simulate Ctrl+key combination.

        Args:
            key: The key to press with Ctrl ('c' for copy, 'v' for paste)
        """
        kbrd = keyboard.Controller()
        with kbrd.pressed(keyboard.Key.ctrl):
            kbrd.press(key)
            kbrd.release(key)

    def _is_file_path(self, text: str) -> bool:
        """Check if text looks like a file path."""
        try:
            from pathlib import Path

            path = Path(text)
            return path.exists() and path.is_file()
        except Exception:
            return False

    # kept for potential future use
    # def _is_file_path(self, text: str) -> bool:
    #     """
    #     Check if the text is a file path (from file/icon selection).

    #     Args:
    #         text: The text to check

    #     Returns:
    #         bool: True if it's a file path, False if it's regular text
    #     """
    #     if not text or not text.strip():
    #         return False

    #     text = text.strip()

    #     # Check for file:// URLs (what we saw in the logs)
    #     if text.startswith("file:///"):
    #         return True

    #     # Check for Windows file paths (C:\, D:\, etc.)
    #     if len(text) > 2 and text[1:3] == ":\\":
    #         return True

    #     # Check for UNC paths (\\server\share)
    #     if text.startswith("\\\\"):
    #         return True

    #     # Check for Unix-style absolute paths
    #     if text.startswith("/") and "/" in text[1:]:
    #         return True

    #     return False
