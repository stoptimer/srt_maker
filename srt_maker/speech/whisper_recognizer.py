import asyncio
import logging
import threading
import wave

import numpy as np

from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry

logger = logging.getLogger(__name__)


class WhisperRecognizer(SpeechRecognizer):
    """OpenAI Whisper 本地语音识别"""

    _model_cache: dict[tuple, tuple] = {}
    _cache_lock = threading.Lock()

    def __init__(self, model_size: str = "base", device: str = "auto"):
        self._model_size = model_size
        self._model = None
        self._device: str = "cpu"
        self._requested_device = device

    def _resolve_device(self) -> str:
        """根据用户选择的设备解析实际设备

        - "auto": 自动检测 GPU
        - "GPU (CUDA)": 强制 GPU，不可用时回退 CPU
        - "CPU": 强制 CPU
        """
        if self._requested_device == "CPU":
            return "cpu"
        if self._requested_device == "GPU (CUDA)":
            import torch
            if torch.cuda.is_available():
                return "cuda"
            # CUDA 不可用时提供详细诊断信息
            cuda_version = getattr(torch.version, "cuda", None)
            if cuda_version is None:
                logger.warning(
                    "用户选择 GPU 但 CUDA 不可用，回退到 CPU。"
                    "原因：PyTorch 是 CPU 版本（%s），不包含 CUDA 支持。"
                    "请安装 GPU 版本：pip install torch --index-url https://download.pytorch.org/whl/cu129",
                    torch.__version__,
                )
            else:
                logger.warning(
                    "用户选择 GPU 但 CUDA 不可用，回退到 CPU。"
                    "PyTorch 版本：%s，CUDA 版本：%s。"
                    "可能原因：CUDA 驱动未安装或版本不兼容",
                    torch.__version__,
                    cuda_version,
                )
            return "cpu"
        # "auto" 或未知值
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self):
        """懒加载 Whisper 模型（使用类级别缓存，支持用户指定设备，线程安全）"""
        cache_key = (self._model_size, self._requested_device)
        if cache_key in WhisperRecognizer._model_cache:
            cached_model, self._device = WhisperRecognizer._model_cache[cache_key]
            self._model = cached_model
            return

        with WhisperRecognizer._cache_lock:
            # 双重检查：获取锁后可能已被其他线程加载
            if cache_key in WhisperRecognizer._model_cache:
                cached_model, self._device = WhisperRecognizer._model_cache[cache_key]
                self._model = cached_model
                return

            import whisper

            device = self._resolve_device()
            self._device = device
            logger.info("加载 Whisper %s 模型，设备: %s", self._model_size, device)
            self._model = whisper.load_model(self._model_size, device=device)
            WhisperRecognizer._model_cache[cache_key] = (self._model, device)

    def name(self) -> str:
        return "Whisper"

    def device_info(self) -> str | None:
        """返回设备信息，内部会触发模型加载"""
        self._load_model()
        if self._device == "cuda":
            return "GPU (CUDA)"
        return "CPU"

    @staticmethod
    def _load_audio_as_array(audio_path: str) -> np.ndarray:
        """将 WAV 音频文件加载为 NumPy 数组

        绕过 Whisper 内部对 FFmpeg 的依赖，直接使用 Python 标准库读取音频。
        音频文件由 AudioExtractor 生成，格式为 16kHz 单声道 PCM 16-bit WAV。

        Args:
            audio_path: WAV 音频文件路径

        Returns:
            float32 类型的 NumPy 数组，值范围 [-1.0, 1.0]

        Raises:
            ValueError: 音频格式不符合预期（16kHz 单声道 PCM 16-bit WAV）
        """
        with wave.open(audio_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            if sample_rate != 16000 or channels != 1:
                raise ValueError(
                    f"音频格式不符合预期：采样率={sample_rate}Hz, 声道数={channels}，"
                    f"预期 16kHz 单声道 PCM 16-bit WAV"
                )
            raw_data = wav_file.readframes(wav_file.getnframes())
        return np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

    async def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表"""
        self._load_model()

        # GPU 上使用 FP16 加速，CPU 上禁用 FP16
        fp16 = (self._device == "cuda")
        logger.info("开始转录，fp16=%s", fp16)

        def _transcribe():
            audio_array = WhisperRecognizer._load_audio_as_array(audio_path)
            return self._model.transcribe(
                audio_array, language=language, verbose=False, fp16=fp16,
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
        logger.info("转录完成，共 %d 条字幕", len(subtitles.entries))
        return subtitles
