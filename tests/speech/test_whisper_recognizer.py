# tests/speech/test_whisper_recognizer.py
import pytest

whisper = pytest.importorskip("whisper")

from srt_maker.speech.whisper_recognizer import WhisperRecognizer
from srt_maker.core.subtitle_list import SubtitleList


def test_whisper_name():
    """测试 Whisper 识别器名称"""
    recognizer = WhisperRecognizer(model_size="tiny")
    assert recognizer.name() == "Whisper"


def test_whisper_instance():
    """测试 Whisper 识别器实例化"""
    recognizer = WhisperRecognizer(model_size="tiny")
    assert recognizer is not None
