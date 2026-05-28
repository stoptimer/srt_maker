import logging

from PySide6.QtCore import QObject, Signal

from srt_maker.video.burner import SubtitleBurner

logger = logging.getLogger(__name__)


class BurnWorker(QObject):
    """字幕烧录工作线程对象

    在 QThread 中执行字幕烧录，避免阻塞 UI 线程。
    """

    progress = Signal(str, int)   # (步骤描述, 百分比)
    finished = Signal()
    error = Signal(str)

    def burn(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_name: str,
        font_size: int,
        color: str,
    ) -> None:
        """执行字幕烧录

        Args:
            video_path: 视频文件路径
            srt_path: SRT 字幕文件路径
            output_path: 输出视频文件路径
            font_name: 字体名称
            font_size: 字体大小
            color: FFmpeg 颜色格式 (如 &H00FFFFFF)
        """
        try:
            self.progress.emit("正在烧录字幕...", 0)
            logger.info("开始烧录: %s -> %s", video_path, output_path)

            burner = SubtitleBurner()
            burner.burn(
                video_path=video_path,
                srt_path=srt_path,
                output_path=output_path,
                font_name=font_name,
                font_size=font_size,
                color=color,
            )

            self.progress.emit("烧录完成", 100)
            logger.info("烧录完成: %s", output_path)
            self.finished.emit()

        except Exception as e:
            logger.error("烧录失败", exc_info=True)
            self.error.emit(str(e))
