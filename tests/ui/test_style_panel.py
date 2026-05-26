import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.style_panel import StylePanel

@pytest.mark.qt_no_exception_capture
def test_style_panel_creation(qtbot):
    """测试样式面板组件可以正常创建"""
    widget = StylePanel()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_style_panel_get_style(qtbot):
    """测试样式面板返回的样式包含必需字段"""
    widget = StylePanel()
    qtbot.add_widget(widget)
    style = widget.get_style()
    assert "font_name" in style
    assert "font_size" in style
    assert "color" in style

@pytest.mark.qt_no_exception_capture
def test_style_panel_default_values(qtbot):
    """测试样式面板默认值正确"""
    widget = StylePanel()
    qtbot.add_widget(widget)
    style = widget.get_style()
    assert style["font_name"] == "微软雅黑"
    assert style["font_size"] == 24

@pytest.mark.qt_no_exception_capture
def test_style_panel_set_style(qtbot):
    """测试设置样式后能正确获取"""
    widget = StylePanel()
    qtbot.add_widget(widget)
    widget.set_style({
        "font_name": "黑体",
        "font_size": 32,
    })
    style = widget.get_style()
    assert style["font_name"] == "黑体"
    assert style["font_size"] == 32
