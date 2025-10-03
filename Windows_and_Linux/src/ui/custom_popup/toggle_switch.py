"""
ToggleSwitch module
Custom toggle switch widget with sliding circle animation.
"""

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp


class ToggleSwitch(QtWidgets.QCheckBox):
    """Custom toggle switch widget with sliding circle animation"""

    toggled = QtCore.Signal(bool)

    def __init__(self, app: "WritingToolsApp", parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.app = app
        self.setFixedSize(50, 24)
        self.setCheckable(True)
        self._circle_position: int = 2
        self._animation = QtCore.QPropertyAnimation(self, b"circle_position")
        self._animation.setDuration(150)

        # Connect native QCheckBox signal to animation
        self.toggled.connect(self._animate_to_position)

    def setChecked(self, arg__1: bool) -> None:
        super().setChecked(arg__1)

    def setCheckable(self, arg__1: bool) -> None:
        super().setCheckable(arg__1)

    @QtCore.Property(int)
    def circle_position(self) -> int:  # type: ignore
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos: int) -> None:
        self._circle_position = pos
        self.update()

    def _animate_to_position(self) -> None:
        start_pos = 2 if not self.isChecked() else 28
        end_pos = 28 if self.isChecked() else 2

        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:  # type: ignore
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Colors from styles
        if self.isChecked():
            bg_color = QtGui.QColor(self.app.styles["color_primary"])
        else:
            bg_color = QtGui.QColor(self.app.styles["color_secondary"])

        circle_color = QtGui.QColor(self.app.styles["color_background"])

        # Draw background
        painter.setBrush(QtGui.QBrush(bg_color))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 50, 24, 12, 12)

        # Draw circle
        painter.setBrush(QtGui.QBrush(circle_color))
        painter.drawEllipse(self._circle_position, 2, 20, 20)
