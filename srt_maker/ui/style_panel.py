from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QSpinBox,
    QFrame, QGridLayout, QColorDialog,
)
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtCore import Qt, Signal

class _ColorFrame(QFrame):
    """可点击的颜色选择框"""

    color_clicked = Signal()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.color_clicked.emit()
        super().mousePressEvent(event)

class StylePanel(QWidget):
    """字幕样式面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(Qt.white)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("字幕样式")
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(label)

        grid = QGridLayout()

        grid.addWidget(QLabel("字体:"), 0, 0)
        self._font_edit = QLineEdit("微软雅黑")
        grid.addWidget(self._font_edit, 0, 1)

        grid.addWidget(QLabel("大小:"), 1, 0)
        self._size_spin = QSpinBox()
        self._size_spin.setRange(8, 72)
        self._size_spin.setValue(24)
        grid.addWidget(self._size_spin, 1, 1)

        grid.addWidget(QLabel("颜色:"), 2, 0)
        self._color_frame = _ColorFrame()
        self._color_frame.setFixedSize(40, 20)
        self._color_frame.setStyleSheet("background-color: white; border: 1px solid #999;")
        self._color_frame.setToolTip("点击选择颜色")
        self._color_frame.setCursor(Qt.PointingHandCursor)
        self._color_frame.color_clicked.connect(self._on_color_clicked)
        grid.addWidget(self._color_frame, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()

    def _on_color_clicked(self):
        """打开颜色选择对话框"""
        dialog = QColorDialog(self._color, self)
        if dialog.exec():
            self._color = dialog.currentColor()
            self._color_frame.setStyleSheet(
                f"background-color: {self._color.name()}; border: 1px solid #999;"
            )

    def get_style(self) -> dict:
        """获取当前样式配置"""
        return {
            "font_name": self._font_edit.text(),
            "font_size": self._size_spin.value(),
            "color": self._color,
        }

    def set_style(self, style: dict):
        """设置样式配置"""
        if "font_name" in style:
            self._font_edit.setText(style["font_name"])
        if "font_size" in style:
            self._size_spin.setValue(style["font_size"])
        if "color" in style:
            self._color = style["color"]
            self._color_frame.setStyleSheet(
                f"background-color: {style['color'].name()}; border: 1px solid #999;"
            )
