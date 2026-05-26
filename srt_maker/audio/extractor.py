# srt_maker/audio/extractor.py
import tempfile
import shutil
from pathlib import Path

from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper


class AudioExtractor:
    """音频提取器 — 从视频提取 16kHz 单声道 PCM 16-bit WAV"""

    def __init__(self, ffmpeg_dir: str = ""):
        self._temp_dir: Path | None = None
        self._audio_path: Path | None = None
        self._ffmpeg = FFmpegWrapper(ffmpeg_dir=ffmpeg_dir)

    def extract(self, video_path: str) -> Path:
        """从视频提取音频，返回临时 WAV 文件路径"""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="srt_maker_"))
        self._audio_path = self._temp_dir / "audio.wav"
        self._ffmpeg.extract_audio(video_path, str(self._audio_path))
        return self._audio_path

    def cleanup(self):
        """清理临时文件"""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
        self._temp_dir = None
        self._audio_path = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
