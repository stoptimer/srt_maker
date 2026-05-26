"""VAD 语音活动检测封装测试"""

import pytest

silero_vad = pytest.importorskip("silero_vad")

from srt_maker.audio.vad import VADDetector


def test_vad_detect_empty():
    """测试空音频检测"""
    detector = VADDetector()
    intervals = detector.detect_empty()
    assert intervals == []


def test_vad_instance():
    """测试 VADDetector 实例化"""
    detector = VADDetector()
    assert detector is not None

    detector_with_path = VADDetector(ffmpeg_dir=r"E:\ffmpeg\bin")
    assert detector_with_path is not None
