"""qwen3-asr 识别器和 VAD 时间轴对齐测试"""

from srt_maker.speech.qwen_asr_recognizer import align_text_with_vad, QwenASRRecognizer
from srt_maker.core.subtitle_model import SubtitleEntry


def test_align_equal_count():
    """测试句子数和区间数相等时的对齐"""
    text = "你好。世界。"
    vad_intervals = [(0.0, 2.0), (2.5, 4.5)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 2
    assert result[0].start_time == 0.0
    assert result[0].end_time == 2.0
    assert result[0].text == "你好"
    assert result[1].text == "世界"


def test_align_more_sentences():
    """测试句子数多于区间数时的对齐"""
    text = "A。B。C。D"
    vad_intervals = [(0.0, 3.0), (4.0, 7.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 2
    # 4 个句子分配到 2 个区间，每个区间 2 个句子
    assert "A" in result[0].text
    assert "C" in result[1].text


def test_align_more_intervals():
    """测试区间数多于句子数时的对齐"""
    text = "你好。"
    vad_intervals = [(0.0, 1.0), (1.5, 2.5), (3.0, 4.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 3
    assert result[0].text == "你好"
    # 多余区间留空
    assert result[1].text == ""
    assert result[2].text == ""


def test_align_empty():
    """测试空文本对齐"""
    result = align_text_with_vad("", [])
    assert len(result) == 0


def test_align_empty_text_with_intervals():
    """测试空文本但有区间时对齐"""
    result = align_text_with_vad("", [(0.0, 1.0)])
    assert len(result) == 0


def test_align_text_without_intervals():
    """测试有文本但无区间时对齐"""
    result = align_text_with_vad("你好", [])
    assert len(result) == 0


def test_align_10_sentences_2_intervals():
    """测试 10 句分配到 2 区间 — 验证所有句子被分配"""
    text = "A。B。C。D。E。F。G。H。I。J"
    vad_intervals = [(0.0, 5.0), (6.0, 10.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 2
    # 10 句均分到 2 区间，每区间 5 句
    assert result[0].text == "ABCDE"
    assert result[1].text == "FGHIJ"

def test_align_3_sentences_2_intervals():
    """测试 3 句分配到 2 区间 — 边界情况"""
    text = "A。B。C"
    vad_intervals = [(0.0, 2.0), (3.0, 5.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 2
    # 3 句分 2 区间：base=1, remainder=1，第一区间 2 句，第二区间 1 句
    assert result[0].text == "AB"
    assert result[1].text == "C"

def test_align_5_sentences_2_intervals():
    """测试 5 句分配到 2 区间 — 不均匀分配"""
    text = "A。B。C。D。E"
    vad_intervals = [(0.0, 3.0), (4.0, 7.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 2
    # 5 句分 2 区间：base=2, remainder=1，第一区间 3 句，第二区间 2 句
    assert result[0].text == "ABC"
    assert result[1].text == "DE"

def test_align_single_sentence_single_interval():
    """测试单句子单区间"""
    text = "你好"
    vad_intervals = [(0.0, 1.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 1
    assert result[0].text == "你好"

def test_qwen_name():
    """测试 qwen3-asr 识别器名称"""
    recognizer = QwenASRRecognizer(api_url="http://localhost:8080")
    assert recognizer.name() == "qwen3-asr"
