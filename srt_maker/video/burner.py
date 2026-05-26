from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

class SubtitleBurner:
    """字幕烧录器"""

    def __init__(self, ffmpeg_dir: str = ""):
        self._ffmpeg = FFmpegWrapper(ffmpeg_dir=ffmpeg_dir)

    def burn(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_name: str = "微软雅黑",
        font_size: int = 24,
        color: str = "&H00FFFFFF",
    ) -> None:
        """将字幕硬编码到视频中"""
        self._ffmpeg.burn_subtitles(
            video_path=video_path,
            srt_path=srt_path,
            output_path=output_path,
            font_name=font_name,
            font_size=font_size,
            color=color,
        )
