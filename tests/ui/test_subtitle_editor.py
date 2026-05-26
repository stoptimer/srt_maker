import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.subtitle_editor import SubtitleEditor
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.core.subtitle_list import SubtitleList

@pytest.mark.qt_no_exception_capture
def test_subtitle_editor_creation(qtbot):
    """测试字幕编辑器组件可以正常创建"""
    widget = SubtitleEditor()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_subtitle_editor_load_data(qtbot):
    """测试字幕编辑器加载数据后行数是正确的"""
    widget = SubtitleEditor()
    qtbot.add_widget(widget)
    subtitles = SubtitleList()
    subtitles.entries.append(SubtitleEntry(1.0, 4.0, "第一条"))
    subtitles.entries.append(SubtitleEntry(5.0, 8.0, "第二条"))
    widget.load_subtitles(subtitles)
    assert widget.row_count() == 2
