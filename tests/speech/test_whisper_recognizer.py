# tests/speech/test_whisper_recognizer.py
import pytest
from unittest.mock import patch, MagicMock

from srt_maker.speech.whisper_recognizer import WhisperRecognizer
from srt_maker.core.subtitle_list import SubtitleList


def test_whisper_name():
    """测试 Whisper 识别器名称"""
    recognizer = WhisperRecognizer(model_size="tiny")
    assert recognizer.name() == "Whisper"


def test_whisper_instance():
    """测试 Whisper 识别器实例化"""
    recognizer = WhisperRecognizer(model_size="tiny")
    assert recognizer is not None


def test_whisper_model_cache():
    """测试 Whisper 模型缓存 — 相同 model_size 返回同一模型"""
    # 清除缓存以确保测试独立性
    WhisperRecognizer._model_cache.clear()

    r1 = WhisperRecognizer(model_size="tiny")
    r2 = WhisperRecognizer(model_size="tiny")

    mock_whisper = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model

    with patch.dict('sys.modules', {'whisper': mock_whisper}):
        # 首次加载
        r1._load_model()
        assert r1._model is not None
        mock_whisper.load_model.assert_called_once_with("tiny")

        # 第二次应从缓存获取
        r2._load_model()
        assert r2._model is r1._model  # 同一实例

        # 模型只加载了一次
        assert mock_whisper.load_model.call_count == 1


def test_whisper_model_cache_different_sizes():
    """测试不同 model_size 加载不同模型"""
    WhisperRecognizer._model_cache.clear()

    r1 = WhisperRecognizer(model_size="tiny")
    r2 = WhisperRecognizer(model_size="base")

    mock_whisper = MagicMock()
    mock_tiny = MagicMock()
    mock_base = MagicMock()
    mock_whisper.load_model.side_effect = [mock_tiny, mock_base]

    with patch.dict('sys.modules', {'whisper': mock_whisper}):
        r1._load_model()
        r2._load_model()

        assert r1._model is mock_tiny
        assert r2._model is mock_base
        assert mock_whisper.load_model.call_count == 2


def test_whisper_transcribe_fp16_disabled():
    """测试 transcribe 调用时正确传递 fp16=False，避免 CPU 上的 FP16 警告"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": []}
    mock_whisper.load_model.return_value = mock_model

    with patch.dict('sys.modules', {'whisper': mock_whisper}):
        recognizer = WhisperRecognizer(model_size="tiny")
        recognizer._load_model()

        import asyncio
        asyncio.run(recognizer.recognize("fake_audio.wav", "zh"))

        # 验证 transcribe 被调用时 fp16=False 是直接的关键字参数
        call_kwargs = mock_model.transcribe.call_args[1]
        assert "fp16" in call_kwargs, "fp16 应该作为关键字参数直接传递"
        assert call_kwargs["fp16"] is False, "fp16 应该为 False"
        # 确保没有嵌套的 decode_options 字典
        assert "decode_options" not in call_kwargs, "不应该有嵌套的 decode_options 字典"
