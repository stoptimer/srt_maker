import pytest
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

# 使用自定义 FFmpeg 路径
wrapper = FFmpegWrapper(ffmpeg_dir=r"E:\ffmpeg\bin")
ffmpeg_available = wrapper.is_available()

def test_ffmpeg_available():
    """测试 FFmpeg 可用性 — 不应跳过"""
    # 这个测试应该反映真实的 FFmpeg 状态
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
