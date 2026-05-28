import logging
from PySide6.QtCore import QObject, Signal

class LogEmitter(QObject):
    """将 Python logging 事件桥接到 Qt Signal"""
    log = Signal(str, str)  # (level, message)

    def emit_log(self, level: str, message: str) -> None:
        self.log.emit(level, message)

class LogHandler(logging.Handler):
    """将日志记录转发到 LogEmitter"""

    def __init__(self, emitter: LogEmitter) -> None:
        super().__init__()
        self.emitter = emitter

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.emitter.emit_log(record.levelname, msg)

def connect_log_to_ui(emitter: LogEmitter) -> LogHandler:
    """将日志连接到 UI 的 LogEmitter

    Returns:
        LogHandler 实例（保存引用防止被垃圾回收）
    """
    lh = LogHandler(emitter)
    lh.setLevel(logging.INFO)
    lh.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))
    logging.getLogger().addHandler(lh)
    return lh
