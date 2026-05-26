import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.video_preview import VideoPreview

@pytest.mark.qt_no_exception_capture
def test_video_preview_creation(qtbot):
    """测试 VideoPreview 组件可以正常创建"""
    widget = VideoPreview()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_video_preview_load_video(qtbot, tmp_path):
    """测试 VideoPreview 可以加载视频并获取时长"""
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    video_path = str(tmp_path / "test.mp4")
    FFmpegWrapper().create_test_video(video_path, duration=2.0)

    widget = VideoPreview()
    qtbot.add_widget(widget)
    widget.load_video(video_path)
    assert widget.duration() > 0
