# srt_maker/speech/whisper_recognizer.py
import asyncio
import wave

import numpy as np

from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry


class WhisperRecognizer(SpeechRecognizer):
    """OpenAI Whisper 本地语音识别"""

    _model_cache: dict[str, object] = {}

    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._model = None

    def _load_model(self):
        """懒加载 Whisper 模型（使用类级别缓存）"""
        if self._model_size in WhisperRecognizer._model_cache:
            self._model = WhisperRecognizer._model_cache[self._model_size]
        else:
            import whisper
            self._model = whisper.load_model(self._model_size)
            WhisperRecognizer._model_cache[self._model_size] = self._model

    def name(self) -> str:
        return "Whisper"

    @staticmethod
    def _load_audio_as_array(audio_path: str) -> np.ndarray:
        """将 WAV 音频文件加载为 NumPy 数组

        绕过 Whisper 内部对 FFmpeg 的依赖，直接使用 Python 标准库读取音频。
        音频文件由 AudioExtractor 生成，格式为 16kHz 单声道 PCM 16-bit WAV。

        Args:
            audio_path: WAV 音频文件路径

        Returns:
            float32 类型的 NumPy 数组，值范围 [-1.0, 1.0]
        """
        with wave.open(audio_path, "rb") as wav_file:
            raw_data = wav_file.readframes(wav_file.getnframes())
        return np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

    async def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表"""
        self._load_model()

        # 在独立线程中执行转录，避免阻塞事件循环
        # 显式禁用 FP16，避免在 CPU 上触发 Whisper 的 FP16 不支持警告
        # 预先将音频加载为 NumPy 数组，避免 Whisper 内部调用 FFmpeg
        def _transcribe():
            audio_array = WhisperRecognizer._load_audio_as_array(audio_path)
            return self._model.transcribe(
                audio_array, language=language, verbose=False, fp16=False,
            )

        result = await asyncio.to_thread(_transcribe)
        subtitles = SubtitleList()
        for segment in result["segments"]:
            entry = SubtitleEntry(
                start_time=segment["start"],
                end_time=segment["end"],
                text=segment["text"].strip(),
            )
            subtitles.entries.append(entry)
        return subtitles
