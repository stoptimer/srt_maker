import os
import sys
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
