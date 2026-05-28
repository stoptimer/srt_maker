from srt_maker.ui.log_viewer import LogViewer


def test_log_viewer_append_info(qtbot):
    """测试 LogViewer 追加 INFO 级别日志"""
    viewer = LogViewer()
    qtbot.add_widget(viewer)

    viewer.append_log("INFO", "测试信息")

    text = viewer.log_text.toPlainText()
    assert "测试信息" in text


def test_log_viewer_append_error_with_color(qtbot):
    """测试 LogViewer 追加 ERROR 级别日志带有颜色"""
    viewer = LogViewer()
    qtbot.add_widget(viewer)

    viewer.append_log("ERROR", "测试错误")

    html = viewer.log_text.toHtml()
    assert "e74c3c" in html  # 红色
    assert "ERROR" in html
    assert "测试错误" in html


def test_log_viewer_append_warning_with_color(qtbot):
    """测试 LogViewer 追加 WARNING 级别日志带有颜色"""
    viewer = LogViewer()
    qtbot.add_widget(viewer)

    viewer.append_log("WARNING", "测试警告")

    html = viewer.log_text.toHtml()
    assert "e67e22" in html  # 橙色
    assert "WARNING" in html


def test_log_viewer_clear(qtbot):
    """测试 LogViewer 清空功能"""
    viewer = LogViewer()
    qtbot.add_widget(viewer)

    viewer.append_log("INFO", "测试")
    viewer.clear_btn.click()

    text = viewer.log_text.toPlainText()
    assert text == ""
