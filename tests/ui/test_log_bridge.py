import logging
from srt_maker.ui.log_bridge import LogEmitter, LogHandler, connect_log_to_ui


def test_log_emitter_signal(qtbot):
    """测试 LogEmitter 发射日志信号"""
    emitter = LogEmitter()
    received = []

    emitter.log.connect(lambda level, msg: received.append((level, msg)))
    emitter.emit_log("INFO", "测试消息")

    assert len(received) == 1
    assert received[0] == ("INFO", "测试消息")


def test_log_handler_forwards_to_emitter(qtbot):
    """测试 LogHandler 将日志记录转发到 LogEmitter"""
    emitter = LogEmitter()
    received = []
    emitter.log.connect(lambda level, msg: received.append((level, msg)))

    handler = LogHandler(emitter)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg="测试日志", args=(), exc_info=None
    )
    handler.emit(record)

    assert len(received) == 1
    assert received[0][0] == "INFO"
    assert "测试日志" in received[0][1]


def test_connect_log_to_ui(qtbot):
    """测试 connect_log_to_ui 将 Handler 添加到根 logger"""
    emitter = LogEmitter()

    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_count = len(root.handlers)

    try:
        handler = connect_log_to_ui(emitter)
        assert isinstance(handler, LogHandler)
        assert len(root.handlers) == original_count + 1
    finally:
        for h in root.handlers[:]:
            root.removeHandler(h)
        for h in original_handlers:
            root.addHandler(h)
