# tests/audio/test_extractor.py
import pytest

from srt_maker.audio.extractor import AudioExtractor
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

wrapper = FFmpegWrapper()
ffmpeg_available = wrapper.is_available()

@pytest.mark.skipif(not ffmpeg_available, reason="FFmpeg 未安装")
def test_extract_audio(tmp_path):
    """测试从视频提取音频"""
    extractor = AudioExtractor()
    video_path = str(tmp_path / "input.mp4")
    FFmpegWrapper().create_test_video(video_path, duration=3.0)

    result = extractor.extract(video_path)
    assert result.exists()
    assert result.suffix == ".wav"
    extractor.cleanup()

@pytest.mark.skipif(not ffmpeg_available, reason="FFmpeg 未安装")
def test_context_manager_cleanup(tmp_path):
    """测试上下文管理器自动清理"""
    video_path = str(tmp_path / "input.mp4")
    FFmpegWrapper().create_test_video(video_path, duration=2.0)

    with AudioExtractor() as extractor:
        audio_path = extractor.extract(video_path)
        assert audio_path.exists()
    # 退出上下文后文件应被清理
    assert not audio_path.exists()
