# srt_maker/speech/whisper_recognizer.py
from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry


class WhisperRecognizer(SpeechRecognizer):
    """OpenAI Whisper 本地语音识别"""

    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._model = None

    def _load_model(self):
        """懒加载 Whisper 模型"""
        if self._model is None:
            import whisper
            self._model = whisper.load_model(self._model_size)

    def name(self) -> str:
        return "Whisper"

    async def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表"""
        self._load_model()
        result = self._model.transcribe(audio_path, language=language, verbose=False)
        subtitles = SubtitleList()
        for segment in result["segments"]:
            entry = SubtitleEntry(
                start_time=segment["start"],
                end_time=segment["end"],
                text=segment["text"].strip(),
            )
            subtitles.entries.append(entry)
        return subtitles
