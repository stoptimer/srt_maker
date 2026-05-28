import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QObject, Signal
from srt_maker.ui.recognition_worker import RecognitionWorker
from srt_maker.core.subtitle_list import SubtitleList


def test_recognition_worker_has_signals():
    """测试 RecognitionWorker 信号定义正确"""
    worker = RecognitionWorker()
    assert hasattr(worker, "progress")
    assert hasattr(worker, "finished")
    assert hasattr(worker, "error")


def test_worker_emits_progress_signals(qtbot):
    """测试 worker 按序发射进度信号"""
    progress_log = []

    worker = RecognitionWorker()
    worker.progress.connect(lambda text, pct: progress_log.append((text, pct)))

    with patch.object(worker, '_create_recognizer') as mock_create:
        mock_recognizer = MagicMock()
        async def mock_recognize(*args):
            return SubtitleList()
        mock_recognizer.recognize = mock_recognize
        mock_create.return_value = mock_recognizer

        with patch('srt_maker.ui.recognition_worker.AudioExtractor') as mock_extractor_cls:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            worker.start("video.mp4", "Whisper", "zh")

    assert len(progress_log) >= 4
    assert progress_log[0][1] == 10   # 提取音频
    assert progress_log[-1][1] == 100  # 识别完成


def test_worker_emits_error_on_exception(qtbot):
    """测试 worker 在异常时发射 error 信号"""
    error_log = []

    worker = RecognitionWorker()
    worker.error.connect(error_log.append)

    with patch('srt_maker.ui.recognition_worker.AudioExtractor') as mock_extractor_cls:
        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = RuntimeError("测试错误")
        mock_extractor_cls.return_value = mock_extractor

        worker.start("video.mp4", "Whisper", "zh")

    assert len(error_log) == 1
    assert "测试错误" in error_log[0]


def test_worker_creates_correct_recognizer(qtbot):
    """测试 worker 创建正确的 Whisper 识别器"""
    worker = RecognitionWorker()
    error_log = []
    worker.error.connect(error_log.append)

    with patch('srt_maker.ui.recognition_worker.WhisperRecognizer') as mock_whisper:
        mock_whisper.return_value = MagicMock()
        # 让识别器创建成功，但 recognize 抛出异常以中断流程
        async def mock_recognize(*args):
            raise RuntimeError("提前中断")
        mock_whisper.return_value.recognize = mock_recognize

        with patch('srt_maker.ui.recognition_worker.AudioExtractor') as mock_extractor_cls:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            worker.start("video.mp4", "Whisper", "zh", "tiny")
            mock_whisper.assert_called_once_with(model_size="tiny")


def test_worker_creates_qwen_recognizer(qtbot):
    """测试 worker 创建 qwen3-asr 识别器"""
    worker = RecognitionWorker()
    error_log = []
    worker.error.connect(error_log.append)

    with patch('srt_maker.ui.recognition_worker.QwenASRRecognizer') as mock_qwen:
        mock_qwen.return_value = MagicMock()
        # 让识别器创建成功，但 recognize 抛出异常以中断流程
        async def mock_recognize(*args):
            raise RuntimeError("提前中断")
        mock_qwen.return_value.recognize = mock_recognize

        with patch('srt_maker.ui.recognition_worker.AudioExtractor') as mock_extractor_cls:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = MagicMock()
            mock_extractor_cls.return_value = mock_extractor

            worker.start("video.mp4", "qwen3-asr", "zh")
            mock_qwen.assert_called_once()


def test_worker_unknown_recognizer_type(qtbot):
    """测试未知识别器类型抛出 ValueError"""
    worker = RecognitionWorker()
    with pytest.raises(ValueError, match="未知的识别器类型"):
        worker._create_recognizer("unknown", "base")


def test_worker_cloud_api_raises_error(qtbot):
    """测试云端 API 未配置时抛出 ValueError"""
    worker = RecognitionWorker()
    with pytest.raises(ValueError, match="云端 API 尚未配置"):
        worker._create_recognizer("云端API", "base")


def test_worker_last_audio_path_property(qtbot):
    """测试 worker 的 last_audio_path 公共属性"""
    worker = RecognitionWorker()
    assert worker.last_audio_path is None


def test_worker_cleanup_on_exception(qtbot):
    """测试异常时 extractor.cleanup() 被调用"""
    worker = RecognitionWorker()
    error_log = []
    worker.error.connect(error_log.append)

    with patch('srt_maker.ui.recognition_worker.AudioExtractor') as mock_extractor_cls:
        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = RuntimeError("提取失败")
        mock_extractor_cls.return_value = mock_extractor

        worker.start("video.mp4", "Whisper", "zh")

    # 异常被捕获并转发
    assert len(error_log) == 1
    assert "提取失败" in error_log[0]
    # cleanup 在 finally 中被调用
    mock_extractor.cleanup.assert_called_once()
