import pytest
from unittest.mock import patch
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

@pytest.mark.qt_no_exception_capture
def test_main_window_has_model_size_combo(qtbot):
    """测试主窗口工具栏包含模型大小下拉框"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert window._model_size_combo is not None
    assert window._model_size_combo.count() == 5
    assert window._model_size_combo.currentText() == "base"

@pytest.mark.qt_no_exception_capture
def test_main_window_has_worker_attributes(qtbot):
    """测试主窗口包含 worker 相关属性"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert hasattr(window, '_worker')
    assert hasattr(window, '_worker_thread')
    assert window._worker is None
    assert window._worker_thread is None

@pytest.mark.qt_no_exception_capture
def test_main_window_has_start_recognition_action(qtbot):
    """测试主窗口有开始识别菜单项"""
    window = MainWindow()
    qtbot.add_widget(window)
    assert hasattr(window, '_start_recognition_action')
    assert window._start_recognition_action.isEnabled()

@pytest.mark.qt_no_exception_capture
def test_main_window_recognition_without_video(qtbot):
    """测试未加载视频时点击开始识别不启动 worker"""
    window = MainWindow()
    qtbot.add_widget(window)
    # Mock QMessageBox 避免对话框阻塞测试
    with patch('srt_maker.ui.main_window.QMessageBox') as mock_msg:
        window._start_recognition()
        # 没有视频时弹出警告
        mock_msg.warning.assert_called_once()
    # 不启动 worker
    assert window._worker is None
    assert window._worker_thread is None

@pytest.mark.qt_no_exception_capture
def test_main_window_recognition_without_ffmpeg(qtbot):
    """测试未安装 FFmpeg 时点击开始识别显示错误提示"""
    window = MainWindow()
    qtbot.add_widget(window)
    window._video_path = "fake_video.mp4"

    with patch('srt_maker.ui.main_window.QMessageBox') as mock_msg:
        with patch('srt_maker.video.ffmpeg_wrapper.FFmpegWrapper') as mock_ffmpeg:
            mock_ffmpeg.return_value.is_available.return_value = False
            window._start_recognition()
            # 没有 FFmpeg 时弹出错误
            mock_msg.critical.assert_called_once()
    # 不启动 worker
    assert window._worker is None
    assert window._worker_thread is None

@pytest.mark.qt_no_exception_capture
def test_main_window_has_settings_menu(qtbot):
    """测试主窗口菜单栏包含设置菜单"""
    window = MainWindow()
    qtbot.add_widget(window)
    menu_bar = window.menuBar()
    # 查找"设置"菜单
    settings_menu = None
    for action in menu_bar.actions():
        if action.text() == "设置":
            settings_menu = action.menu()
            break
    assert settings_menu is not None
    # 检查设置菜单中有"设置"动作
    assert any(action.text() == "设置" for action in settings_menu.actions())
