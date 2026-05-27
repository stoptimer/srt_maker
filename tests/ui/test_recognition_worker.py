import pytest
from PySide6.QtCore import QObject, Signal
from srt_maker.ui.recognition_worker import RecognitionWorker


def test_recognition_worker_has_signals():
    """测试 RecognitionWorker 信号定义正确"""
    worker = RecognitionWorker()
    assert hasattr(worker, "progress")
    assert hasattr(worker, "finished")
    assert hasattr(worker, "error")
