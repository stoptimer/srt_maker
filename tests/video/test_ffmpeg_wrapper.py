import pytest
from pathlib import Path
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper, _split_long_subtitles
from srt_maker.core.subtitle_model import SubtitleEntry

wrapper = FFmpegWrapper()
ffmpeg_available = wrapper.is_available()

def test_ffmpeg_available():
    """测试 FFmpeg 可用性 — 不应跳过"""
    assert isinstance(wrapper.is_available(), bool)

@pytest.mark.skipif(not ffmpeg_available, reason="FFmpeg 未安装")
def test_get_video_duration(tmp_path):
    """测试获取视频时长"""
    video_path = str(tmp_path / "test.mp4")
    wrapper.create_test_video(video_path, duration=5.0)
    duration = wrapper.get_duration(video_path)
    assert abs(duration - 5.0) < 0.5

@pytest.mark.skipif(not ffmpeg_available, reason="FFmpeg 未安装")
def test_extract_audio(tmp_path):
    """测试从视频提取音频"""
    video_path = str(tmp_path / "test.mp4")
    audio_path = str(tmp_path / "test.wav")
    wrapper.create_test_video(video_path, duration=2.0)
    wrapper.extract_audio(video_path, audio_path)
    import os
    assert os.path.exists(audio_path)

@pytest.mark.skipif(not ffmpeg_available, reason="FFmpeg 未安装")
def test_create_test_video(tmp_path):
    """测试创建测试视频"""
    video_path = str(tmp_path / "test.mp4")
    wrapper.create_test_video(video_path, duration=3.0)
    import os
    assert os.path.exists(video_path)
    assert os.path.getsize(video_path) > 0

def test_bundled_ffmpeg_dir_returns_empty_when_not_found(tmp_path):
    """打包目录下没有 FFmpeg 时返回空字符串"""
    from srt_maker.video.ffmpeg_wrapper import _bundled_ffmpeg_dir
    # 不在打包环境中，_MEIPASS 不存在
    result = _bundled_ffmpeg_dir()
    assert result == ""

def test_ffmpeg_dir_from_config_when_env_not_set(tmp_path):
    """测试 FFmpegWrapper 从配置文件读取 ffmpeg_dir（即使环境变量未设置）

    回归测试：修复了模块级 _DEFAULT_FFMPEG_DIR 在环境变量设置前就被求值的问题。
    重启程序后，FFmpegWrapper 应该能从 config.json 读取 FFmpeg 路径。
    """
    import json
    import os

    # 创建一个包含 ffmpeg.exe 的目录
    ffmpeg_dir = tmp_path / "ffmpeg"
    ffmpeg_dir.mkdir()
    (ffmpeg_dir / "ffmpeg.exe").touch()

    # 模拟配置文件中有 ffmpeg_dir
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({"ffmpeg_dir": str(ffmpeg_dir)}), encoding="utf-8")

    # 模拟配置文件路径指向我们的临时目录
    import srt_maker.core.config as config_mod
    original_config_file = config_mod._CONFIG_FILE
    config_mod._CONFIG_FILE = config_file

    # 确保环境变量没有设置
    old_env = os.environ.pop("FFMPEG_DIR", None)

    try:
        wrapper = FFmpegWrapper()
        # _resolve_ffmpeg_dir 应该从配置文件读取到 ffmpeg_dir
        assert wrapper._ffmpeg_dir == str(ffmpeg_dir), \
            f"期望从配置文件读取 {ffmpeg_dir}，实际: {wrapper._ffmpeg_dir}"
    finally:
        config_mod._CONFIG_FILE = original_config_file
        if old_env is not None:
            os.environ["FFMPEG_DIR"] = old_env


def test_bundled_ffmpeg_dir_finds_ffmpeg_in_meipass(tmp_path, monkeypatch):
    """打包目录下有 FFmpeg 时返回正确路径"""
    import sys
    # 模拟 PyInstaller 目录结构：_MEIPASS 指向 _internal/，ffmpeg/ 在其父目录
    meipass_dir = tmp_path / "_internal"
    meipass_dir.mkdir()
    ffmpeg_dir = tmp_path / "ffmpeg"
    ffmpeg_dir.mkdir()
    (ffmpeg_dir / "ffmpeg.exe").touch()
    # sys 是内置模块，setattr 会失败，需要用 object.__setattr__ 绕过
    object.__setattr__(sys, "_MEIPASS", str(meipass_dir))
    # 需要重新导入以拾取新的 _MEIPASS
    from srt_maker.video.ffmpeg_wrapper import _bundled_ffmpeg_dir
    result = _bundled_ffmpeg_dir()
    assert Path(result).resolve() == ffmpeg_dir.resolve()
    # 清理
    delattr(sys, "_MEIPASS")


def test_split_long_subtitles_skips_short_entries():
    """短字幕不被拆分"""
    entries = [SubtitleEntry(0.0, 1.0, "Short text")]
    result = _split_long_subtitles(entries)
    assert len(result) == 1
    assert result[0].text == "Short text"


def test_split_long_subtitles_splits_long_entry():
    """超长字幕被拆分为多条"""
    long_text = "This is a very very long subtitle that would normally wrap and get clipped"
    entries = [SubtitleEntry(0.0, 3.0, long_text)]
    result = _split_long_subtitles(entries)
    assert len(result) > 1
    # 每条不超过 40 字符
    for e in result:
        assert len(e.text) <= 40
    # 时间区间覆盖原始范围
    assert result[0].start_time == 0.0
    assert result[-1].end_time == 3.0
    # 时间区间连续无重叠
    for i in range(1, len(result)):
        assert abs(result[i].start_time - result[i - 1].end_time) < 0.001


def test_split_long_subtitles_preserves_time_order():
    """拆分后时间顺序正确"""
    entries = [
        SubtitleEntry(1.0, 3.0, "First short subtitle"),
        SubtitleEntry(4.0, 8.0, "This is a very very long subtitle that needs to be split into multiple parts"),
        SubtitleEntry(9.0, 10.0, "Last short subtitle"),
    ]
    result = _split_long_subtitles(entries)
    # 第一条和最后一条不变
    assert result[0].text == "First short subtitle"
    assert result[-1].text == "Last short subtitle"
    # 中间条被拆分
    middle_splits = result[1:-1]
    assert len(middle_splits) > 1
    # 拆分条目时间范围在原始区间内
    assert middle_splits[0].start_time >= 4.0
    assert middle_splits[-1].end_time <= 8.0


def test_split_long_subtitles_breaks_at_word_boundaries():
    """拆分在单词边界处断开"""
    long_text = "one two three four five six seven eight nine ten eleven twelve thirteen"
    entries = [SubtitleEntry(0.0, 2.0, long_text)]
    result = _split_long_subtitles(entries)
    # 每条不应该在单词中间断开
    for e in result:
        parts = e.text.split()
        for part in parts:
            assert part in long_text.split()
