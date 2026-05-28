# 字幕烧录功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现从 UI 触发字幕硬编码烧录到视频的完整流程。

**Architecture:** 核心引擎（`SubtitleBurner` + `FFmpegWrapper.burn_subtitles`）已完整实现。新增 `BurnWorker` 作为后台工作器，遵循 `RecognitionWorker` 的 QThread + Worker 模式。主窗口 `_burn_subtitles()` 负责前置检查、临时文件管理、样式转换和 worker 生命周期。

**Tech Stack:** PySide6 (QThread, QObject, Signal), FFmpeg, tempfile

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `srt_maker/ui/burn_worker.py` | 新建 | `BurnWorker` — 后台烧录工作器 |
| `srt_maker/ui/main_window.py` | 修改 | `_burn_subtitles()` 完整实现 + 信号处理 + worker 清理 |
| `tests/ui/test_burn_worker.py` | 新建 | `BurnWorker` 单元测试 |

---

### Task 1: 创建 BurnWorker

**Files:**
- Create: `srt_maker/ui/burn_worker.py`
- Test: `tests/ui/test_burn_worker.py`

- [ ] **Step 1: Write the failing test — BurnWorker 信号定义**

```python
# tests/ui/test_burn_worker.py
import pytest
from PySide6.QtCore import QObject, Signal
from srt_maker.ui.burn_worker import BurnWorker


def test_burn_worker_has_signals():
    """测试 BurnWorker 信号定义正确"""
    worker = BurnWorker()
    assert hasattr(worker, "progress")
    assert hasattr(worker, "finished")
    assert hasattr(worker, "error")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_burn_worker.py::test_burn_worker_has_signals -v`
Expected: FAIL with ImportError (module does not exist yet)

- [ ] **Step 3: Create BurnWorker**

```python
# srt_maker/ui/burn_worker.py
import logging
import os
import tempfile

from PySide6.QtCore import QObject, Signal

from srt_maker.video.burner import SubtitleBurner

logger = logging.getLogger(__name__)


class BurnWorker(QObject):
    """字幕烧录工作线程对象

    在 QThread 中执行字幕烧录，避免阻塞 UI 线程。
    """

    progress = Signal(str, int)   # (步骤描述, 百分比)
    finished = Signal()
    error = Signal(str)

    def burn(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_name: str,
        font_size: int,
        color: str,
    ) -> None:
        """执行字幕烧录

        Args:
            video_path: 视频文件路径
            srt_path: SRT 字幕文件路径
            output_path: 输出视频文件路径
            font_name: 字体名称
            font_size: 字体大小
            color: FFmpeg 颜色格式 (如 &H00FFFFFF)
        """
        try:
            self.progress.emit("正在烧录字幕...", 0)
            logger.info("开始烧录: %s -> %s", video_path, output_path)

            burner = SubtitleBurner()
            burner.burn(
                video_path=video_path,
                srt_path=srt_path,
                output_path=output_path,
                font_name=font_name,
                font_size=font_size,
                color=color,
            )

            self.progress.emit("烧录完成", 100)
            logger.info("烧录完成: %s", output_path)
            self.finished.emit()

        except Exception as e:
            logger.error("烧录失败", exc_info=True)
            self.error.emit(str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/ui/test_burn_worker.py::test_burn_worker_has_signals -v`
Expected: PASS

- [ ] **Step 5: Write test — BurnWorker 发射 error 信号**

Add to `tests/ui/test_burn_worker.py`:

```python
def test_burn_worker_emits_error_on_exception(qtbot):
    """测试 BurnWorker 在烧录失败时发射 error 信号"""
    error_log = []
    worker = BurnWorker()
    worker.error.connect(error_log.append)

    with pytest.raises(NameError):  # 确保 burner.burn 调用失败
        pass  # 我们用 patch 来模拟

    from unittest.mock import patch
    with patch.object(worker, '__class__', create=True) as mock_cls:
        pass  # 更简单的方式：直接 mock SubtitleBurner

    # 正确方式：mock SubtitleBurner.burn 抛出异常
    with patch('srt_maker.ui.burn_worker.SubtitleBurner') as mock_burner_cls:
        mock_burner = MagicMock()
        mock_burner.burn.side_effect = RuntimeError("烧录失败")
        mock_burner_cls.return_value = mock_burner

        worker.start_burn(
            video_path="video.mp4",
            srt_path="sub.srt",
            output_path="out.mp4",
            font_name="微软雅黑",
            font_size=24,
            color="&H00FFFFFF",
        )

    assert len(error_log) == 1
    assert "烧录失败" in error_log[0]
```

> **修正**: 上面的测试方法有问题，`burn` 方法签名已确定，不应改成 `start_burn`。重写测试：

```python
from unittest.mock import patch, MagicMock

def test_burn_worker_emits_error_on_exception(qtbot):
    """测试 BurnWorker 在烧录失败时发射 error 信号"""
    error_log = []
    worker = BurnWorker()
    worker.error.connect(error_log.append)

    with patch('srt_maker.ui.burn_worker.SubtitleBurner') as mock_burner_cls:
        mock_burner = MagicMock()
        mock_burner.burn.side_effect = RuntimeError("烧录失败")
        mock_burner_cls.return_value = mock_burner

        worker.burn(
            video_path="video.mp4",
            srt_path="sub.srt",
            output_path="out.mp4",
            font_name="微软雅黑",
            font_size=24,
            color="&H00FFFFFF",
        )

    assert len(error_log) == 1
    assert "烧录失败" in error_log[0]
```

- [ ] **Step 6: Run error test**

Run: `pytest tests/ui/test_burn_worker.py::test_burn_worker_emits_error_on_exception -v`
Expected: PASS

- [ ] **Step 7: Write test — BurnWorker 成功时发射 finished 信号**

Add to `tests/ui/test_burn_worker.py`:

```python
def test_burn_worker_emits_finished_on_success(qtbot):
    """测试 BurnWorker 烧录成功时发射 finished 信号"""
    finished_log = []
    worker = BurnWorker()
    worker.finished.connect(finished_log.append)

    with patch('srt_maker.ui.burn_worker.SubtitleBurner') as mock_burner_cls:
        mock_burner = MagicMock()
        mock_burner_cls.return_value = mock_burner

        worker.burn(
            video_path="video.mp4",
            srt_path="sub.srt",
            output_path="out.mp4",
            font_name="微软雅黑",
            font_size=24,
            color="&H00FFFFFF",
        )

    assert len(finished_log) == 1
    mock_burner.burn.assert_called_once_with(
        video_path="video.mp4",
        srt_path="sub.srt",
        output_path="out.mp4",
        font_name="微软雅黑",
        font_size=24,
        color="&H00FFFFFF",
    )
```

- [ ] **Step 8: Run all Task 1 tests**

Run: `pytest tests/ui/test_burn_worker.py -v`
Expected: All 3 tests PASS

- [ ] **Step 9: Commit**

```bash
git add srt_maker/ui/burn_worker.py tests/ui/test_burn_worker.py
git commit -m "feat: 添加 BurnWorker 后台烧录工作器及测试"
```

---

### Task 2: QColor 转 FFmpeg 颜色格式

**Files:**
- Modify: `srt_maker/ui/main_window.py`

- [ ] **Step 1: Write the failing test — 颜色格式转换**

Add to `tests/ui/test_burn_worker.py`:

```python
def test_qcolor_to_ffmpeg_color():
    """测试 QColor 转 FFmpeg 颜色格式"""
    from PySide6.QtGui import QColor
    from srt_maker.ui.main_window import _qcolor_to_ffmpeg_color

    # 白色
    assert _qcolor_to_ffmpeg_color(QColor(255, 255, 255)) == "&H00FFFFFF"

    # 红色 (R=255, G=0, B=0 → BGR: 0000FF)
    assert _qcolor_to_ffmpeg_color(QColor(255, 0, 0)) == "&H000000FF"

    # 黄色 (R=255, G=255, B=0 → BGR: 00FFFF)
    assert _qcolor_to_ffmpeg_color(QColor(255, 255, 0)) == "&H0000FFFF"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_burn_worker.py::test_qcolor_to_ffmpeg_color -v`
Expected: FAIL with ImportError (function not defined yet)

- [ ] **Step 3: Add color conversion function to main_window.py**

Add at the top of `srt_maker/ui/main_window.py`, after the existing imports. Add `QColor` to the PySide6.QtGui import (new import line):

```python
from PySide6.QtGui import QColor
```

Add the helper function right before the `MainWindow` class:

```python
def _qcolor_to_ffmpeg_color(color: QColor) -> str:
    """QColor 转 FFmpeg 颜色格式 &H00RRGGBB（BGR 字节序）"""
    return f"&H00{color.blue():02X}{color.green():02X}{color.red():02X}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/ui/test_burn_worker.py::test_qcolor_to_ffmpeg_color -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add srt_maker/ui/main_window.py tests/ui/test_burn_worker.py
git commit -m "feat: 添加 QColor 转 FFmpeg 颜色格式转换函数"
```

---

### Task 3: 完善 _burn_subtitles() 方法

**Files:**
- Modify: `srt_maker/ui/main_window.py:306-313`

- [ ] **Step 1: Add burn worker member variables to MainWindow.__init__**

In `MainWindow.__init__`, after `self._worker_thread: QThread | None = None`, add:

```python
self._burn_worker: "BurnWorker" | None = None
self._burn_worker_thread: QThread | None = None
```

Also add the import at the top of the file (after the existing imports from srt_maker.ui):

```python
from srt_maker.ui.burn_worker import BurnWorker
```

- [ ] **Step 2: Replace _burn_subtitles() stub with full implementation**

Replace lines 306-313 of `srt_maker/ui/main_window.py`:

```python
    def _burn_subtitles(self):
        if not self._video_path:
            QMessageBox.warning(self, "提示", "请先打开视频文件")
            return
        if not self._subtitles.entries:
            QMessageBox.warning(self, "提示", "请先加载字幕")
            return

        # 检查 FFmpeg 是否可用
        from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
        if not FFmpegWrapper().is_available():
            QMessageBox.critical(
                self, "错误",
                "未找到 FFmpeg，请先安装 FFmpeg 并将其添加到系统 PATH 中，\n"
                "或通过设置配置 FFmpeg 路径。"
            )
            return

        # 将字幕写入临时 SRT 文件
        srt_fd, srt_path = tempfile.mkstemp(suffix=".srt", prefix="srt_maker_")
        try:
            with os.fdopen(srt_fd, "w", encoding="utf-8") as f:
                f.write(write_srt(self._subtitles.entries))
        except Exception:
            os.unlink(srt_path)
            raise

        # 获取样式
        style = self.style_panel.get_style()
        font_name = style["font_name"]
        font_size = style["font_size"]
        color = _qcolor_to_ffmpeg_color(style["color"])

        # 选择输出路径
        video_name = Path(self._video_path).stem
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存烧录视频",
            f"{video_name}_with_subtitles.mp4",
            "视频文件 (*.mp4)",
        )
        if not output_path:
            os.unlink(srt_path)
            return

        # 创建 worker 和线程
        self._burn_worker = BurnWorker()
        self._burn_worker_thread = QThread()

        self._burn_worker.moveToThread(self._burn_worker_thread)

        # 连接信号
        self._burn_worker_thread.started.connect(
            lambda: self._burn_worker.burn(
                self._video_path,
                srt_path,
                output_path,
                font_name,
                font_size,
                color,
            )
        )
        self._burn_worker.progress.connect(self._on_burn_progress)
        self._burn_worker.finished.connect(self._on_burn_finished)
        self._burn_worker.error.connect(self._on_burn_error)

        # 保存临时文件路径用于清理
        self._burn_srt_path = srt_path

        # 启动
        self.progress.setVisible(True)
        self.progress.setMaximum(0)  # 不定长模式
        self.statusBar().showMessage("烧录中...")
```

Add `tempfile` and `os` to the imports at the top of `main_window.py`, and `Path` from `pathlib`:

```python
import os
import tempfile
from pathlib import Path
```

- [ ] **Step 3: Add _on_burn_progress() handler**

```python
    def _on_burn_progress(self, text: str, percentage: int):
        """更新烧录进度"""
        self.progress.setValue(percentage)
        self.statusBar().showMessage(text)
```

- [ ] **Step 4: Add _on_burn_finished() handler**

```python
    def _on_burn_finished(self):
        """烧录完成"""
        # 清理临时 SRT 文件
        if hasattr(self, '_burn_srt_path') and self._burn_srt_path:
            try:
                os.unlink(self._burn_srt_path)
            except OSError:
                pass

        self.statusBar().showMessage("烧录完成")
        self._cleanup_burn_worker()
```

- [ ] **Step 5: Add _on_burn_error() handler**

```python
    def _on_burn_error(self, message: str):
        """烧录失败"""
        # 清理临时 SRT 文件
        if hasattr(self, '_burn_srt_path') and self._burn_srt_path:
            try:
                os.unlink(self._burn_srt_path)
            except OSError:
                pass

        QMessageBox.critical(self, "烧录失败", message)
        self._cleanup_burn_worker()
```

- [ ] **Step 6: Add _cleanup_burn_worker() handler**

```python
    def _cleanup_burn_worker(self):
        """清理烧录工作线程资源"""
        if self._burn_worker_thread:
            self._burn_worker_thread.quit()
            if not self._burn_worker_thread.wait(5000):
                self._burn_worker_thread.terminate()
                self._burn_worker_thread.wait()
            self._burn_worker_thread.deleteLater()
            self._burn_worker_thread = None
        if self._burn_worker:
            self._burn_worker.deleteLater()
            self._burn_worker = None
        self.progress.setVisible(False)
        self.progress.setMaximum(100)  # 恢复定长模式
        self.progress.setValue(0)
```

- [ ] **Step 7: Run all tests to verify no regressions**

Run: `pytest tests/ui/test_burn_worker.py tests/ui/test_recognition_worker.py -v`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add srt_maker/ui/main_window.py
git commit -m "feat: 实现 _burn_subtitles 完整烧录流程和信号处理"
```

---

### Task 4: 集成测试 — BurnWorker 与 SubtitleBurner 端到端

**Files:**
- Modify: `tests/ui/test_burn_worker.py`

- [ ] **Step 1: Write integration test — BurnWorker 调用 SubtitleBurner**

Add to `tests/ui/test_burn_worker.py`:

```python
@pytest.mark.skipif(
    not FFmpegWrapper().is_available(),
    reason="FFmpeg 未安装",
)
def test_burn_worker_integration(qtbot):
    """测试 BurnWorker 端到端烧录流程"""
    import os

    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

    wrapper = FFmpegWrapper()

    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = os.path.join(tmp_dir, "input.mp4")
        wrapper.create_test_video(video_path, duration=3.0)

        srt_path = os.path.join(tmp_dir, "sub.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(write_srt([SubtitleEntry(0.5, 1.5, "测试字幕")]))

        output_path = os.path.join(tmp_dir, "output.mp4")

        finished_log = []
        error_log = []
        worker = BurnWorker()
        worker.finished.connect(finished_log.append)
        worker.error.connect(error_log.append)

        # 直接调用 burn（非异步，测试中不需要 QThread）
        worker.burn(
            video_path=video_path,
            srt_path=srt_path,
            output_path=output_path,
            font_name="微软雅黑",
            font_size=24,
            color="&H00FFFFFF",
        )

        assert len(finished_log) == 1
        assert len(error_log) == 0
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
```

- [ ] **Step 2: Add required imports to test file**

At the top of `tests/ui/test_burn_worker.py`, ensure these imports:

```python
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor

from srt_maker.ui.burn_worker import BurnWorker
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.io.srt_parser import write_srt
```

- [ ] **Step 3: Run all Task 4 tests**

Run: `pytest tests/ui/test_burn_worker.py -v`
Expected: All 4 tests PASS (1 skipped if FFmpeg unavailable)

- [ ] **Step 4: Commit**

```bash
git add tests/ui/test_burn_worker.py
git commit -m "test: 添加 BurnWorker 集成测试和颜色转换测试"
```

---

### Task 5: 运行完整测试套件验证

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`
Expected: All existing tests PASS, no regressions

- [ ] **Step 2: Manual verification (optional — requires UI)**

1. 启动程序: `python -m srt_maker.main`
2. 打开一个视频文件
3. 添加字幕（或执行语音识别生成字幕）
4. 调整样式面板中的字体/大小/颜色
5. 点击"烧录字幕"按钮
6. 选择输出路径
7. 确认烧录完成，输出视频包含字幕

- [ ] **Step 3: Final commit if any fixes needed**

If test fixes were needed during verification:

```bash
git add -A
git commit -m "fix: 修复测试中发现的问题"
```
