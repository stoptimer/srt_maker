import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.waveform_view import WaveformView

@pytest.mark.qt_no_exception_capture
def test_waveform_creation(qtbot):
    """测试 WaveformView 组件可以正常创建"""
    widget = WaveformView()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_waveform_load_audio(qtbot, tmp_path):
    """测试 WaveformView 可以加载音频并显示波形"""
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    audio_path = str(tmp_path / "test.wav")
    FFmpegWrapper().create_test_video(str(tmp_path / "test.mp4"), duration=2.0)
    FFmpegWrapper().extract_audio(str(tmp_path / "test.mp4"), audio_path)

    widget = WaveformView()
    qtbot.add_widget(widget)
    widget.load_audio(audio_path)
    assert widget._audio_data is not None

@pytest.mark.qt_no_exception_capture
def test_waveform_highlight_subtitle(qtbot, tmp_path):
    """测试 WaveformView 高亮字幕区间"""
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    audio_path = str(tmp_path / "test.wav")
    FFmpegWrapper().create_test_video(str(tmp_path / "test.mp4"), duration=2.0)
    FFmpegWrapper().extract_audio(str(tmp_path / "test.mp4"), audio_path)

    widget = WaveformView()
    qtbot.add_widget(widget)
    widget.load_audio(audio_path)
    widget.highlight_subtitle(0.5, 1.0)
    assert len(widget._subtitle_regions) == 1

@pytest.mark.qt_no_exception_capture
def test_waveform_clear_highlights(qtbot, tmp_path):
    """测试 WaveformView 清除高亮"""
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    audio_path = str(tmp_path / "test.wav")
    FFmpegWrapper().create_test_video(str(tmp_path / "test.mp4"), duration=2.0)
    FFmpegWrapper().extract_audio(str(tmp_path / "test.mp4"), audio_path)

    widget = WaveformView()
    qtbot.add_widget(widget)
    widget.load_audio(audio_path)
    widget.highlight_subtitle(0.5, 1.0)
    widget.highlight_subtitle(1.0, 1.5)
    assert len(widget._subtitle_regions) == 2

    widget.clear_highlights()
    assert len(widget._subtitle_regions) == 0
