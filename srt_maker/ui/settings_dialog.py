"""设置对话框 — FFmpeg 路径配置"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from srt_maker.core.config import load_config, save_config
from srt_maker.video import ffmpeg_wrapper


class SettingsDialog(QDialog):
    """设置对话框 — FFmpeg 路径配置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)
        self._setup_ui()
        self._load_current_config()

    def _setup_ui(self):
        """设置界面布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # FFmpeg 路径
        label = QLabel("FFmpeg 路径")
        layout.addWidget(label)

        path_layout = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        path_layout.addWidget(self._path_edit, 1)

        self._browse_btn = QPushButton("浏览...")
        self._browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self._browse_btn)

        layout.addLayout(path_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._reset_btn = QPushButton("重置")
        self._reset_btn.clicked.connect(self._reset_path)
        btn_layout.addWidget(self._reset_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _load_current_config(self):
        """加载当前配置并显示"""
        config = load_config()
        ffmpeg_dir = config.get("ffmpeg_dir", "")
        self._path_edit.setText(ffmpeg_dir)

    def _browse_path(self):
        """打开文件夹选择对话框"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择 FFmpeg 目录"
        )
        if directory:
            self._path_edit.setText(directory)

    def _reset_path(self):
        """清空 FFmpeg 路径"""
        self._path_edit.setText("")

    def _save(self):
        """保存配置"""
        ffmpeg_dir = self._path_edit.text().strip()

        if ffmpeg_dir:
            # 验证 ffmpeg.exe 是否存在
            ffmpeg_exe = Path(ffmpeg_dir) / "ffmpeg.exe"
            if not ffmpeg_exe.exists():
                QMessageBox.warning(
                    self, "路径无效",
                    f"在所选目录中未找到 ffmpeg.exe\n\n请选择 FFmpeg 的 bin 目录。"
                )
                return

        # 保存配置
        config = load_config()
        config["ffmpeg_dir"] = ffmpeg_dir
        save_config(config)

        # 更新 FFmpegWrapper 的默认路径，使当前会话生效
        ffmpeg_wrapper._DEFAULT_FFMPEG_DIR = ffmpeg_dir
        if ffmpeg_dir:
            os.environ["FFMPEG_DIR"] = ffmpeg_dir
        elif "FFMPEG_DIR" in os.environ:
            del os.environ["FFMPEG_DIR"]

        QMessageBox.information(self, "保存成功", "FFmpeg 路径已更新")
        self.accept()
