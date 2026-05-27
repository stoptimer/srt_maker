# srt_maker/speech/whisper_recognizer.py
import asyncio

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

    async def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表"""
        self._load_model()

        # 在独立线程中执行转录，避免阻塞事件循环
        # 显式禁用 FP16，避免在 CPU 上触发 Whisper 的 FP16 不支持警告
        def _transcribe():
            return self._model.transcribe(
                audio_path, language=language, verbose=False, fp16=False,
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
