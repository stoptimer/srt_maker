import os
import sys

# 必须在所有 import 之前设置，避免 PyTorch 和 PySide6 的 OpenMP DLL 冲突
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 在主线程中预加载 PyTorch，避免在工作线程中加载时出现 WinError 1114
# PyTorch 的 DLL 初始化需要在主线程的 COM apartment 中完成
try:
    import torch  # noqa: F401
except ImportError:
    pass  # PyTorch 未安装时忽略，识别时会给出更明确的提示

from PySide6.QtWidgets import QApplication
from srt_maker.core.config import load_config
from srt_maker.core.logger import setup_logging
from srt_maker.ui.log_bridge import LogEmitter, connect_log_to_ui
from srt_maker.ui.main_window import MainWindow

def main():
    # 加载配置并设置环境变量
    config = load_config()
    if config.get("ffmpeg_dir"):
        os.environ["FFMPEG_DIR"] = config["ffmpeg_dir"]

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 初始化日志（文件 + 控制台）
    setup_logging()

    # 连接日志到 UI
    emitter = LogEmitter()
    window = MainWindow()
    log_handler = connect_log_to_ui(emitter)

    # 连接日志信号到主窗口的日志面板（QueuedConnection 确保 UI 更新在主线程）
    if hasattr(window, 'log_viewer'):
        from PySide6.QtCore import Qt
        emitter.log.connect(window.log_viewer.append_log, Qt.QueuedConnection)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
