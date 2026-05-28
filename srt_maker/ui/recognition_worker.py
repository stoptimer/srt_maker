import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.audio.extractor import AudioExtractor
from srt_maker.speech.whisper_recognizer import WhisperRecognizer
from srt_maker.speech.qwen_asr_recognizer import QwenASRRecognizer
from srt_maker.speech.cloud_recognizer import CloudSpeechRecognizer

logger = logging.getLogger(__name__)


class RecognitionWorker(QObject):
    """语音识别工作线程对象

    在 QThread 中执行完整的识别流程：
    音频提取 → 识别器调用 → 结果返回
    """

    progress = Signal(str, int)       # (步骤描述, 百分比)
    finished = Signal(object)         # SubtitleList 实例
    error = Signal(str)               # 错误信息

    def __init__(self):
        super().__init__()
        self._last_audio_path: Path | None = None

    @property
    def last_audio_path(self) -> Path | None:
        """返回上次提取的音频文件路径"""
        return self._last_audio_path

    def start(
        self,
        video_path: str,
        recognizer_type: str,
        language: str,
        model_size: str = "base",
    ) -> None:
        """执行识别流程

        Args:
            video_path: 视频文件路径
            recognizer_type: 识别器类型 ("Whisper", "qwen3-asr", "云端API")
            language: 语言代码 ("zh", "en", "auto")
            model_size: Whisper 模型大小（仅 Whisper 使用）
        """
        extractor = None
        try:
            logger.info("=== 识别流程开始 ===")
            logger.info("视频: %s", video_path)
            logger.info("识别器: %s, 模型: %s, 语言: %s",
                        recognizer_type, model_size, language)

            # 1. 提取音频
            self.progress.emit("正在提取音频...", 10)
            logger.info("开始提取音频")
            extractor = AudioExtractor()
            audio_path = extractor.extract(video_path)
            self._last_audio_path = audio_path
            logger.info("音频提取完成: %s", audio_path)

            # 2. 创建识别器
            self.progress.emit("正在加载模型...", 20)
            recognizer = self._create_recognizer(recognizer_type, model_size)

            # 预加载模型以获取设备信息
            if hasattr(recognizer, '_load_model'):
                recognizer._load_model()

            device = getattr(recognizer, '_device', None)
            if device:
                device_text = "GPU (CUDA)" if device == "cuda" else "CPU"
                self.progress.emit(f"使用 {device_text}", 25)
                logger.info("识别设备: %s", device_text)

            # 3. 执行识别（在独立线程中执行，避免阻塞 Qt 事件循环）
            self.progress.emit("正在识别语音...", 50)
            subtitles = self._recognize_sync(recognizer, str(audio_path), language)

            # 4. 处理结果
            self.progress.emit("正在处理结果...", 90)
            logger.info("识别完成，共 %d 条字幕", len(subtitles.entries))

            self.progress.emit("识别完成", 100)
            self.finished.emit(subtitles)

        except Exception as e:
            logger.error("识别流程失败", exc_info=True)
            self.error.emit(str(e))

        finally:
            if extractor is not None:
                extractor.cleanup()

    def _create_recognizer(
        self,
        recognizer_type: str,
        model_size: str,
    ) -> "SpeechRecognizer":
        """根据类型创建识别器实例

        Args:
            recognizer_type: 识别器类型
            model_size: Whisper 模型大小

        Returns:
            识别器实例

        Raises:
            ValueError: 未知的识别器类型
        """
        if recognizer_type == "Whisper":
            return WhisperRecognizer(model_size=model_size)
        elif recognizer_type == "qwen3-asr":
            return QwenASRRecognizer()
        elif recognizer_type == "云端API":
            raise ValueError("云端 API 尚未配置，请先在设置中配置 API Key")
        else:
            raise ValueError(f"未知的识别器类型: {recognizer_type}")

    def _recognize_sync(
        self,
        recognizer: "SpeechRecognizer",
        audio_path: str,
        language: str,
    ) -> SubtitleList:
        """在独立线程中同步执行识别，避免 asyncio 与 Qt 事件循环冲突"""
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(recognizer.recognize(audio_path, language))
        finally:
            loop.close()
