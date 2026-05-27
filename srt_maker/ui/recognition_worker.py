import asyncio
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.audio.extractor import AudioExtractor
from srt_maker.speech.whisper_recognizer import WhisperRecognizer
from srt_maker.speech.qwen_asr_recognizer import QwenASRRecognizer
from srt_maker.speech.cloud_recognizer import CloudSpeechRecognizer


class RecognitionWorker(QObject):
    """语音识别工作线程对象

    在 QThread 中执行完整的识别流程：
    音频提取 → 识别器调用 → 结果返回
    """

    progress = Signal(str, int)       # (步骤描述, 百分比)
    finished = Signal(object)         # SubtitleList 实例
    error = Signal(str)               # 错误信息

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
        try:
            # 1. 提取音频
            self.progress.emit("正在提取音频...", 10)
            extractor = AudioExtractor()
            audio_path = extractor.extract(video_path)

            # 2. 创建识别器
            self.progress.emit("正在加载模型...", 20)
            recognizer = self._create_recognizer(recognizer_type, model_size)

            # 3. 执行识别
            self.progress.emit("正在识别语音...", 50)
            subtitles = asyncio.run(recognizer.recognize(str(audio_path), language))

            # 4. 处理结果
            self.progress.emit("正在处理结果...", 90)

            # 5. 清理临时文件
            extractor.cleanup()

            self.progress.emit("识别完成", 100)
            self.finished.emit(subtitles)

        except Exception as e:
            self.error.emit(str(e))

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
            # TODO: 从设置中读取 API key 和 URL
            return CloudSpeechRecognizer(api_key="")
        else:
            raise ValueError(f"未知的识别器类型: {recognizer_type}")
