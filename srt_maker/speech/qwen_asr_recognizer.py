"""qwen3-asr 语音识别器（通过 llama.cpp API）+ VAD 时间轴对齐"""

import re

import requests

from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.audio.vad import VADDetector


def _split_sentences(text: str) -> list[str]:
    """按中文/英文标点分句

    Args:
        text: 待分句的文本

    Returns:
        去除空白后的句子列表
    """
    sentences = re.split(r"[，。！？；.!?;]+", text)
    return [s.strip() for s in sentences if s.strip()]


def align_text_with_vad(
    text: str,
    vad_intervals: list[tuple[float, float]],
) -> list[SubtitleEntry]:
    """将无时间轴的文字与 VAD 区间对齐

    当句子数等于区间数时逐一对应；句子数少于区间数时多余区间留空；
    句子数多于区间数时按比例合并相邻句子。

    Args:
        text: 无时间轴的纯文本
        vad_intervals: VAD 检测到的语音区间列表

    Returns:
        对齐后的字幕条目列表
    """
    if not text or not vad_intervals:
        return []

    sentences = _split_sentences(text)
    entries: list[SubtitleEntry] = []

    if len(sentences) <= len(vad_intervals):
        # 句子数 <= 区间数：逐一对应，多余区间留空
        for i, (start, end) in enumerate(vad_intervals):
            if i < len(sentences):
                entries.append(SubtitleEntry(start, end, sentences[i]))
            else:
                entries.append(SubtitleEntry(start, end, ""))
    else:
        # 句子数 > 区间数：按区间均匀分配句子，最后一个区间取剩余全部
        import math
        base_count = len(sentences) // len(vad_intervals)
        remainder = len(sentences) % len(vad_intervals)
        sentence_idx = 0

        for idx, (start, end) in enumerate(vad_intervals):
            # 前 remainder 个区间多分 1 句
            num_sentences = base_count + (1 if idx < remainder else 0)
            merged = "".join(sentences[sentence_idx:sentence_idx + num_sentences])
            entries.append(SubtitleEntry(start, end, merged))
            sentence_idx += num_sentences

    return entries


class QwenASRRecognizer(SpeechRecognizer):
    """qwen3-asr 语音识别器（通过 llama.cpp API）+ VAD 时间轴对齐

    工作流程：
        1. 调用 qwen3-asr API 获取纯文本
        2. 通过 Silero VAD 检测语音区间
        3. 将文本分句后与 VAD 区间对齐生成字幕
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8080",
        ffmpeg_dir: str = "",
    ):
        """初始化 qwen3-asr 识别器

        Args:
            api_url: llama.cpp API 地址
            ffmpeg_dir: ffmpeg 可执行文件所在目录，为空则从 PATH 查找
        """
        self._api_url = api_url
        self._vad = VADDetector(ffmpeg_dir=ffmpeg_dir)

    def name(self) -> str:
        return "qwen3-asr"

    async def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表

        Args:
            audio_path: 音频文件路径（16kHz 单声道 PCM 16-bit WAV）
            language: 语言代码（如 "zh"、"en"）

        Returns:
            字幕列表

        Raises:
            requests.RequestException: API 调用失败
            RuntimeError: VAD 检测失败
        """
        # 1. 调用 qwen3-asr API 获取文字
        text = self._call_api(audio_path)

        # 2. VAD 检测语音区间
        vad_intervals = self._vad.detect(audio_path)

        # 3. 文字与时间轴对齐
        entries = align_text_with_vad(text, vad_intervals)
        subtitles = SubtitleList()
        subtitles.entries = entries
        return subtitles

    def _call_api(self, audio_path: str) -> str:
        """调用 qwen3-asr API 进行语音识别

        Args:
            audio_path: 音频文件路径

        Returns:
            识别出的纯文本

        Raises:
            requests.RequestException: 网络请求失败
        """
        with open(audio_path, "rb") as f:
            response = requests.post(
                f"{self._api_url}/inference",
                files={"file": ("audio.wav", f, "audio/wav")},
                timeout=300,
            )
        response.raise_for_status()
        data = response.json()
        return data.get("text", "").strip()
