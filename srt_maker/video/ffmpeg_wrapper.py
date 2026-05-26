import subprocess
import os
from pathlib import Path

# 默认 FFmpeg 路径（可通过环境变量或构造参数覆盖）
_DEFAULT_FFMPEG_DIR = os.environ.get("FFMPEG_DIR", "")

class FFmpegWrapper:
    """FFmpeg 命令行封装"""

    def __init__(self, ffmpeg_dir: str = ""):
        """
        初始化 FFmpeg 封装。

        Args:
            ffmpeg_dir: FFmpeg 可执行文件所在目录，默认从 FFMPEG_DIR 环境变量读取，
                        若为空则从 PATH 中查找
        """
        self._ffmpeg_dir = ffmpeg_dir or _DEFAULT_FFMPEG_DIR

    def _ffmpeg_cmd(self) -> str:
        """返回 ffmpeg 可执行文件路径"""
        if self._ffmpeg_dir:
            return str(Path(self._ffmpeg_dir) / "ffmpeg.exe")
        return "ffmpeg"

    def _ffprobe_cmd(self) -> str:
        """返回 ffprobe 可执行文件路径"""
        if self._ffmpeg_dir:
            return str(Path(self._ffmpeg_dir) / "ffprobe.exe")
        return "ffprobe"

    def is_available(self) -> bool:
        """检查 FFmpeg 是否可用"""
        try:
            subprocess.run(
                [self._ffmpeg_cmd(), "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        cmd = [
            self._ffprobe_cmd(), "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())

    def extract_audio(self, video_path: str, output_path: str) -> None:
        """从视频提取音频为 16kHz 单声道 PCM 16-bit WAV"""
        cmd = [
            self._ffmpeg_cmd(), "-i", video_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-sample_fmt", "s16", "-c:a", "pcm_s16le",
            "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=300)

    def create_test_video(self, output_path: str, duration: float = 5.0) -> None:
        """创建测试视频（黑色画面，静音）"""
        cmd = [
            self._ffmpeg_cmd(),
            "-f", "lavfi", "-i", f"color=c=black:s=640x480:d={duration}",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=60)

    def burn_subtitles(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_name: str = "微软雅黑",
        font_size: int = 24,
        color: str = "&H00FFFFFF",
    ) -> None:
        """将字幕硬编码到视频中"""
        style = f"Fontname={font_name},FontSize={font_size},PrimaryColour={color}"
        cmd = [
            self._ffmpeg_cmd(),
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style={style}",
            "-c:a", "copy",
            "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=600)
