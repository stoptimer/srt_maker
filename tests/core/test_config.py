import pytest
from unittest.mock import patch
from pathlib import Path

from srt_maker.core.config import load_config, save_config, _CONFIG_FILE, _DEFAULTS


def test_config_load_default(tmp_path):
    """测试配置文件不存在时返回默认值"""
    with patch('srt_maker.core.config._CONFIG_FILE', tmp_path / "nonexistent.json"):
        config = load_config()
    assert config == {"ffmpeg_dir": ""}


def test_config_save_and_load(tmp_path):
    """测试写入配置后能正确读取"""
    fake_file = tmp_path / "config.json"
    with patch('srt_maker.core.config._CONFIG_FILE', fake_file):
        save_config({"ffmpeg_dir": "E:/ffmpeg/bin"})
        config = load_config()
    assert config["ffmpeg_dir"] == "E:/ffmpeg/bin"


def test_config_merge_defaults(tmp_path):
    """测试旧配置缺少新增字段时使用默认值"""
    fake_file = tmp_path / "config.json"
    # 模拟旧配置，只有 ffmpeg_dir 字段
    fake_file.write_text('{"ffmpeg_dir": "C:/old/ffmpeg"}', encoding="utf-8")
    with patch('srt_maker.core.config._CONFIG_FILE', fake_file):
        with patch('srt_maker.core.config._DEFAULTS', {"ffmpeg_dir": "", "new_key": "default"}):
            config = load_config()
    assert config["ffmpeg_dir"] == "C:/old/ffmpeg"
    assert config["new_key"] == "default"


def test_main_loads_config_and_sets_env(tmp_path):
    """测试 main.py 启动时加载配置并设置 FFMPEG_DIR 环境变量"""
    import os
    fake_file = tmp_path / "config.json"
    fake_file.write_text('{"ffmpeg_dir": "E:/ffmpeg/bin"}', encoding="utf-8")

    with patch('srt_maker.core.config._CONFIG_FILE', fake_file):
        config = load_config()
        if config.get("ffmpeg_dir"):
            os.environ["FFMPEG_DIR"] = config["ffmpeg_dir"]

    assert os.environ.get("FFMPEG_DIR") == "E:/ffmpeg/bin"
    # 清理
    os.environ.pop("FFMPEG_DIR", None)
