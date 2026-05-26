# srt_maker/speech/base.py
from abc import ABC, abstractmethod

from srt_maker.core.subtitle_list import SubtitleList


class SpeechRecognizer(ABC):
    """语音识别器抽象基类

    所有语音识别实现（Whisper、qwen3-asr、云端 API）均需继承此类
    并实现 recognize 和 name 方法。
    """

    @abstractmethod
    def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表

        Args:
            audio_path: 音频文件路径（16kHz 单声道 PCM 16-bit WAV）
            language: 语言代码（如 "zh"、"en"）

        Returns:
            字幕列表
        """
        ...

    @abstractmethod
    def name(self) -> str:
        """返回识别器名称（用于 UI 显示）

        Returns:
            识别器名称字符串
        """
        ...
