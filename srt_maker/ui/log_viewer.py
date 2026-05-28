from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout

class LogViewer(QWidget):
    """日志查看面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont("Consolas, 9")
        layout.addWidget(self.log_text, 1)

        btn_layout = QHBoxLayout()
        self.open_btn = QPushButton("打开日志文件")
        self.open_btn.clicked.connect(self._open_log_file)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.log_text.clear)
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def append_log(self, level: str, message: str) -> None:
        """追加日志条目，根据级别着色"""
        color = {"WARNING": "#e67e22", "ERROR": "#e74c3c"}.get(level, "#333")
        self.log_text.append(
            f'<span style="color:{color}">[{level}]</span> {message}'
        )

    def _open_log_file(self) -> None:
        from srt_maker.core.logger import get_log_file_path
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(get_log_file_path())))
