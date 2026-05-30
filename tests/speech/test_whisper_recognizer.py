# tests/speech/test_whisper_recognizer.py
import numpy as np
import tempfile
import threading
import wave
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
    WhisperRecognizer._model_cache.clear()

    r1 = WhisperRecognizer(model_size="tiny")
    r2 = WhisperRecognizer(model_size="tiny")

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        # 首次加载
        r1._load_model()
        assert r1._model is not None
        mock_whisper.load_model.assert_called_once_with("tiny", device="cpu")

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
    mock_torch = MagicMock()
    mock_tiny = MagicMock()
    mock_base = MagicMock()
    mock_whisper.load_model.side_effect = [mock_tiny, mock_base]
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        r1._load_model()
        r2._load_model()

        assert r1._model is mock_tiny
        assert r2._model is mock_base
        assert mock_whisper.load_model.call_count == 2


def test_whisper_transcribe_fp16_disabled():
    """测试 transcribe 调用时正确传递 fp16=False（CPU 模式）"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": []}
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        with patch.object(WhisperRecognizer, '_load_audio_as_array') as mock_load:
            mock_load.return_value = np.zeros(16000, dtype=np.float32)

            recognizer = WhisperRecognizer(model_size="tiny")
            recognizer._load_model()

            import asyncio
            asyncio.run(recognizer.recognize("fake_audio.wav", "zh"))

            # 验证音频被加载为 NumPy 数组（而非文件路径传给 Whisper）
            mock_load.assert_called_once_with("fake_audio.wav")

            # 验证 transcribe 的第一个参数是 NumPy 数组而非文件路径
            call_args = mock_model.transcribe.call_args[0]
            assert isinstance(call_args[0], np.ndarray), "transcribe 应该接收 NumPy 数组而非文件路径"

            # 验证 transcribe 被调用时 fp16=False 是直接的关键字参数
            call_kwargs = mock_model.transcribe.call_args[1]
            assert "fp16" in call_kwargs, "fp16 应该作为关键字参数直接传递"
            assert call_kwargs["fp16"] is False, "fp16 应该为 False"
            # 确保没有嵌套的 decode_options 字典
            assert "decode_options" not in call_kwargs, "不应该有嵌套的 decode_options 字典"


def test_whisper_gpu_device_selection():
    """测试 GPU 可用时选择 CUDA 设备"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny")
        recognizer._load_model()

        mock_whisper.load_model.assert_called_once_with("tiny", device="cuda")
        assert recognizer._device == "cuda"


def test_whisper_cpu_fallback():
    """测试 GPU 不可用时回退到 CPU"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny")
        recognizer._load_model()

        mock_whisper.load_model.assert_called_once_with("tiny", device="cpu")
        assert recognizer._device == "cpu"


def test_whisper_fp16_on_cuda():
    """测试 CUDA 设备上 fp16=True"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": []}
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        with patch.object(WhisperRecognizer, '_load_audio_as_array') as mock_load:
            mock_load.return_value = np.zeros(16000, dtype=np.float32)

            recognizer = WhisperRecognizer(model_size="tiny")
            recognizer._load_model()

            import asyncio
            asyncio.run(recognizer.recognize("fake.wav", "zh"))

            call_kwargs = mock_model.transcribe.call_args[1]
            assert call_kwargs["fp16"] is True

        mock_model.transcribe.return_value = {"segments": []}


def test_whisper_fp16_false_on_cpu():
    """测试 CPU 设备上 fp16=False"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": []}
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        with patch.object(WhisperRecognizer, '_load_audio_as_array') as mock_load:
            mock_load.return_value = np.zeros(16000, dtype=np.float32)

            recognizer = WhisperRecognizer(model_size="tiny")
            recognizer._load_model()

            import asyncio
            asyncio.run(recognizer.recognize("fake.wav", "zh"))

            call_kwargs = mock_model.transcribe.call_args[1]
            assert call_kwargs["fp16"] is False


def test_whisper_model_cache_preserves_device():
    """测试模型缓存命中时 device 正确恢复"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        r1 = WhisperRecognizer(model_size="tiny")
        r1._load_model()
        assert r1._device == "cuda"

        r2 = WhisperRecognizer(model_size="tiny")
        r2._load_model()
        assert r2._device == "cuda"

        assert mock_whisper.load_model.call_count == 1


def test_whisper_device_info_gpu():
    """测试 device_info() 返回 GPU (CUDA) 当 GPU 可用"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny")
        device_text = recognizer.device_info()
        assert device_text == "GPU (CUDA)"


def test_whisper_device_info_cpu():
    """测试 device_info() 返回 CPU 当 GPU 不可用"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny")
        device_text = recognizer.device_info()
        assert device_text == "CPU"


def test_whisper_model_cache_thread_safety():
    """测试模型缓存使用双重检查锁定——并发加载同一模型只加载一次"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        results = []

        def load_in_thread():
            r = WhisperRecognizer(model_size="tiny")
            r._load_model()
            results.append(r._model)

        threads = [threading.Thread(target=load_in_thread) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有线程应获得同一模型实例
        assert len(set(id(r) for r in results)) == 1, "所有线程应获得同一模型实例"
        # 模型只加载了一次
        assert mock_whisper.load_model.call_count == 1, "模型应只加载一次"


def test_whisper_device_auto_gpu():
    """测试 device="auto" 且 GPU 可用时选择 CUDA"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny", device="auto")
        recognizer._load_model()

        mock_whisper.load_model.assert_called_once_with("tiny", device="cuda")
        assert recognizer._device == "cuda"


def test_whisper_device_auto_cpu():
    """测试 device="auto" 且 GPU 不可用时选择 CPU"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny", device="auto")
        recognizer._load_model()

        mock_whisper.load_model.assert_called_once_with("tiny", device="cpu")
        assert recognizer._device == "cpu"


def test_whisper_device_force_gpu():
    """测试 device="GPU (CUDA)" 强制使用 GPU"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny", device="GPU (CUDA)")
        recognizer._load_model()

        mock_whisper.load_model.assert_called_once_with("tiny", device="cuda")
        assert recognizer._device == "cuda"


def test_whisper_device_force_gpu_unavailable():
    """测试 device="GPU (CUDA)" 但 GPU 不可用时回退 CPU"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = False
    mock_torch.__version__ = "2.0.0+cpu"
    mock_torch.version.cuda = None  # CPU 版本没有 CUDA

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny", device="GPU (CUDA)")
        recognizer._load_model()

        # 回退到 CPU
        mock_whisper.load_model.assert_called_once_with("tiny", device="cpu")
        assert recognizer._device == "cpu"


def test_whisper_device_force_cpu():
    """测试 device="CPU" 强制使用 CPU（即使 GPU 可用）"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        recognizer = WhisperRecognizer(model_size="tiny", device="CPU")
        recognizer._load_model()

        mock_whisper.load_model.assert_called_once_with("tiny", device="cpu")
        assert recognizer._device == "cpu"


def test_whisper_cache_different_devices():
    """测试相同 model_size 不同 device 缓存为不同条目"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_gpu_model = MagicMock()
    mock_cpu_model = MagicMock()
    mock_whisper.load_model.side_effect = [mock_gpu_model, mock_cpu_model]
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        r_gpu = WhisperRecognizer(model_size="tiny", device="GPU (CUDA)")
        r_cpu = WhisperRecognizer(model_size="tiny", device="CPU")

        r_gpu._load_model()
        r_cpu._load_model()

        assert r_gpu._model is mock_gpu_model
        assert r_cpu._model is mock_cpu_model
        assert r_gpu._device == "cuda"
        assert r_cpu._device == "cpu"
        assert mock_whisper.load_model.call_count == 2


def test_whisper_cache_same_model_size_and_device():
    """测试相同 model_size 和 device 共享缓存"""
    WhisperRecognizer._model_cache.clear()

    mock_whisper = MagicMock()
    mock_torch = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_torch.cuda.is_available.return_value = True

    with patch.dict('sys.modules', {'whisper': mock_whisper, 'torch': mock_torch}):
        r1 = WhisperRecognizer(model_size="tiny", device="GPU (CUDA)")
        r2 = WhisperRecognizer(model_size="tiny", device="GPU (CUDA)")

        r1._load_model()
        r2._load_model()

        assert r1._model is r2._model
        assert mock_whisper.load_model.call_count == 1


def test_load_audio_as_array():
    """测试 _load_audio_as_array 将 WAV 文件正确加载为 NumPy 数组"""
    # 创建一个测试 WAV 文件（16kHz 单声道 PCM 16-bit）
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name

    try:
        # 写入已知的音频数据
        expected_data = np.sin(np.linspace(0, 2 * np.pi, 16000)).astype(np.float32)
        int16_data = (expected_data * 32767).astype(np.int16)

        with wave.open(wav_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(int16_data.tobytes())

        # 加载音频
        audio = WhisperRecognizer._load_audio_as_array(wav_path)

        # 验证类型和范围
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert audio.shape == (16000,)
        assert audio.min() >= -1.0
        assert audio.max() <= 1.0

        # 验证数据正确性（int16 -> float32 归一化后的正弦波）
        # expected_data 是 [-1, 1] 范围的 float32，写入 WAV 时 * 32767 转为 int16，
        # 读取时 / 32768 归一化，所以期望值是 expected_data * 32767 / 32768
        expected_normalized = expected_data * 32767.0 / 32768.0
        np.testing.assert_array_almost_equal(audio, expected_normalized, decimal=3)
    finally:
        import os
        os.unlink(wav_path)




def test_load_audio_wrong_sample_rate():
    """Test WAV sample rate mismatch raises ValueError"""
    import wave
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    try:
        with wave.open(tmp_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(b"\x00" * 100)

        with pytest.raises(ValueError):
            WhisperRecognizer._load_audio_as_array(tmp_path)
    finally:
        os.unlink(tmp_path)


def test_load_audio_wrong_channels():
    """Test WAV channel count mismatch raises ValueError"""
    import wave
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    try:
        with wave.open(tmp_path, "wb") as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b"\x00" * 100)

        with pytest.raises(ValueError):
            WhisperRecognizer._load_audio_as_array(tmp_path)
    finally:
        os.unlink(tmp_path)
