import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.main_window import MainWindow

@pytest.mark.qt_no_exception_capture
def test_main_window_creation(qtbot):
    """测试主窗口可以正常创建并设置标题"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window is not None
    assert window.windowTitle() == "SRT Maker"

@pytest.mark.qt_no_exception_capture
def test_main_window_has_video_preview(qtbot):
    """测试主窗口包含视频预览组件"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window.video_preview is not None

@pytest.mark.qt_no_exception_capture
def test_main_window_has_waveform(qtbot):
    """测试主窗口包含波形图组件"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window.waveform is not None

@pytest.mark.qt_no_exception_capture
def test_main_window_has_subtitle_editor(qtbot):
    """测试主窗口包含字幕编辑器组件"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window.subtitle_editor is not None

@pytest.mark.qt_no_exception_capture
def test_main_window_has_style_panel(qtbot):
    """测试主窗口包含样式面板组件"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window.style_panel is not None

@pytest.mark.qt_no_exception_capture
def test_main_window_has_progress_bar(qtbot):
    """测试主窗口包含进度条"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window.progress is not None

@pytest.mark.qt_no_exception_capture
def test_main_window_has_recognizer_combo(qtbot):
    """测试主窗口工具栏包含识别方式下拉框"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window._recognizer_combo is not None
    assert window._recognizer_combo.count() == 3

@pytest.mark.qt_no_exception_capture
def test_main_window_has_language_combo(qtbot):
    """测试主窗口工具栏包含语言下拉框"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window._language_combo is not None
    assert window._language_combo.count() == 3
