"""Silero VAD 语音活动检测封装"""

import subprocess
from pathlib import Path


class VADDetector:
    """Silero VAD 语音活动检测封装"""

    def __init__(self, ffmpeg_dir: str = ""):
        """初始化 VAD 检测器

        Args:
            ffmpeg_dir: ffmpeg 可执行文件所在目录，为空则从 PATH 查找
        """
        self._ffmpeg_dir = ffmpeg_dir
        self._model = None
        self._utils = None

    def _load_model(self):
        """懒加载 Silero VAD 模型"""
        if self._model is None:
            import torch
            import silero_vad

            self._model, self._utils = silero_vad.load_silero_vad()

    def _ffmpeg_cmd(self) -> str:
        """返回 ffmpeg 可执行文件路径"""
        if self._ffmpeg_dir:
            return str(Path(self._ffmpeg_dir) / "ffmpeg.exe")
        return "ffmpeg"

    def detect(self, audio_path: str) -> list[tuple[float, float]]:
        """检测音频中的语音区间，返回 [(start_sec, end_sec), ...]

        Args:
            audio_path: 音频文件路径

        Returns:
            语音区间列表，每个区间为 (起始秒数，结束秒数) 的元组

        Raises:
            subprocess.TimeoutExpired: FFmpeg 处理超时
            RuntimeError: FFmpeg 执行失败
        """
        self._load_model()
        get_speech_timestamps = self._utils["get_speech_timestamps"]

        import numpy as np
        import torch

        cmd = [
            self._ffmpeg_cmd(),
            "-i",
            audio_path,
            "-f",
            "f32le",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-",
        ]
        result = subprocess.run(
            cmd, capture_output=True, timeout=300
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg 执行失败: {result.stderr.decode('utf-8', errors='replace')}"
            )

        audio = np.frombuffer(result.stdout, dtype=np.float32)

        timestamps = get_speech_timestamps(
            torch.from_numpy(audio),
            self._model,
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=100,
        )

        return [
            (ts["start"] / 16000.0, ts["end"] / 16000.0)
            for ts in timestamps
        ]

    def detect_empty(self) -> list[tuple[float, float]]:
        """空音频返回空列表"""
        return []
