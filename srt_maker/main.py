import os
import sys

# 在主线程中预加载 PyTorch，避免在工作线程中加载时出现 WinError 1114
# PyTorch 的 DLL 初始化需要在主线程的 COM apartment 中完成
try:
    import torch  # noqa: F401
except ImportError:
    pass  # PyTorch 未安装时忽略，识别时会给出更明确的提示

from PySide6.QtWidgets import QApplication
from srt_maker.core.config import load_config
from srt_maker.ui.main_window import MainWindow

def main():
    # 加载配置并设置环境变量
    config = load_config()
    if config.get("ffmpeg_dir"):
        os.environ["FFMPEG_DIR"] = config["ffmpeg_dir"]

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
