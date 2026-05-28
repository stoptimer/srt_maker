import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtGui import QColor
from srt_maker.ui.burn_worker import BurnWorker
from srt_maker.ui.main_window import _qcolor_to_ffmpeg_color


def test_burn_worker_has_signals():
    """测试 BurnWorker 信号定义正确"""
    worker = BurnWorker()
    assert hasattr(worker, "progress")
    assert hasattr(worker, "finished")
    assert hasattr(worker, "error")


def test_burn_worker_emits_error_on_exception(qtbot):
    """测试 BurnWorker 在烧录失败时发射 error 信号"""
    error_log = []
    worker = BurnWorker()
    worker.error.connect(error_log.append)

    with patch('srt_maker.ui.burn_worker.SubtitleBurner') as mock_burner_cls:
        mock_burner = MagicMock()
        mock_burner.burn.side_effect = RuntimeError("烧录失败")
        mock_burner_cls.return_value = mock_burner

        worker.burn(
            video_path="video.mp4",
            srt_path="sub.srt",
            output_path="out.mp4",
            font_name="微软雅黑",
            font_size=24,
            color="&H00FFFFFF",
        )

    assert len(error_log) == 1
    assert "烧录失败" in error_log[0]


def test_burn_worker_emits_progress_signals(qtbot):
    """测试 BurnWorker 烧录过程发射进度信号"""
    progress_log = []
    worker = BurnWorker()
    worker.progress.connect(lambda text, pct: progress_log.append((text, pct)))

    with patch('srt_maker.ui.burn_worker.SubtitleBurner') as mock_burner_cls:
        mock_burner = MagicMock()
        mock_burner_cls.return_value = mock_burner

        worker.burn(
            video_path="video.mp4",
            srt_path="sub.srt",
            output_path="out.mp4",
            font_name="微软雅黑",
            font_size=24,
            color="&H00FFFFFF",
        )

    assert len(progress_log) == 2
    assert progress_log[0] == ("正在烧录字幕...", 0)
    assert progress_log[1] == ("烧录完成", 100)


def test_burn_worker_emits_finished_on_success(qtbot):
    """测试 BurnWorker 烧录成功时发射 finished 信号"""
    finished_log = []
    worker = BurnWorker()
    worker.finished.connect(lambda: finished_log.append(True))

    with patch('srt_maker.ui.burn_worker.SubtitleBurner') as mock_burner_cls:
        mock_burner = MagicMock()
        mock_burner_cls.return_value = mock_burner

        worker.burn(
            video_path="video.mp4",
            srt_path="sub.srt",
            output_path="out.mp4",
            font_name="微软雅黑",
            font_size=24,
            color="&H00FFFFFF",
        )

    assert len(finished_log) == 1
    mock_burner.burn.assert_called_once_with(
        video_path="video.mp4",
        srt_path="sub.srt",
        output_path="out.mp4",
        font_name="微软雅黑",
        font_size=24,
        color="&H00FFFFFF",
    )


def test_qcolor_to_ffmpeg_color():
    """测试 QColor 转 FFmpeg 颜色格式"""
    # 白色
    assert _qcolor_to_ffmpeg_color(QColor(255, 255, 255)) == "&H00FFFFFF"

    # 红色 (R=255, G=0, B=0 → BGR: 0000FF)
    assert _qcolor_to_ffmpeg_color(QColor(255, 0, 0)) == "&H000000FF"

    # 黄色 (R=255, G=255, B=0 → BGR: 00FFFF)
    assert _qcolor_to_ffmpeg_color(QColor(255, 255, 0)) == "&H0000FFFF"
