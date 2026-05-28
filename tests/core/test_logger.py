import logging
import tempfile
from pathlib import Path

from srt_maker.core.logger import setup_logging, get_log_file_path


def test_setup_logging_creates_file():
    """测试 setup_logging 创建日志文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        import srt_maker.core.logger as logger_mod
        original = logger_mod._CONFIG_DIR
        try:
            logger_mod._CONFIG_DIR = Path(tmpdir) / ".srt_maker"
            logger_mod._LOG_FILE = logger_mod._CONFIG_DIR / "srt_maker.log"

            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)

            setup_logging()

            log_file = get_log_file_path()
            assert log_file.exists(), "日志文件应该被创建"
            assert logger_mod._CONFIG_DIR.exists(), "配置目录应该被创建"
        finally:
            logger_mod._CONFIG_DIR = original
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)


def test_get_log_file_path():
    """测试 get_log_file_path 返回正确的路径"""
    path = get_log_file_path()
    assert path.name == "srt_maker.log"


def test_setup_logging_writes_log():
    """测试日志能够写入文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        import srt_maker.core.logger as logger_mod
        original_dir = logger_mod._CONFIG_DIR
        original_file = logger_mod._LOG_FILE
        try:
            logger_mod._CONFIG_DIR = Path(tmpdir) / ".srt_maker"
            logger_mod._LOG_FILE = logger_mod._CONFIG_DIR / "srt_maker.log"

            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)

            setup_logging()

            test_logger = logging.getLogger("test_gpu_plan")
            test_logger.info("测试日志条目")

            log_file = get_log_file_path()
            content = log_file.read_text(encoding="utf-8")
            assert "测试日志条目" in content
        finally:
            logger_mod._CONFIG_DIR = original_dir
            logger_mod._LOG_FILE = original_file
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
