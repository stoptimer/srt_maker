import pytest
from pathlib import Path
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

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
