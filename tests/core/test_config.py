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
