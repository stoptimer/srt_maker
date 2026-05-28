import logging
from pathlib import Path

_CONFIG_DIR = Path(Path.home() / ".srt_maker")
_LOG_FILE = _CONFIG_DIR / "srt_maker.log"

def setup_logging() -> None:
    """初始化日志系统（全局调用一次）

    配置根 logger：
    - FileHandler → 写入日志文件（DEBUG 及以上）
    - StreamHandler → 输出到控制台（INFO 及以上）
    """
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # 文件 Handler（记录所有级别）
    fh = logging.FileHandler(str(_LOG_FILE), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root.addHandler(fh)

    # 控制台 Handler（只输出 INFO 及以上）
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))
    root.addHandler(ch)

def get_log_file_path() -> Path:
    """返回日志文件路径"""
    return _LOG_FILE
