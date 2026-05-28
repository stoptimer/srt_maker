# 字幕烧录功能设计

**目标:** 实现从 UI 触发字幕硬编码烧录到视频的完整流程。

**架构:** 核心引擎（`SubtitleBurner` + `FFmpegWrapper.burn_subtitles`）已完整实现，仅需补齐 UI 集成层。采用与语音识别相同的 QThread + Worker 异步模式。

---

## 已有组件（无需修改）

| 组件 | 文件 | 说明 |
|------|------|------|
| `SubtitleBurner` | `srt_maker/video/burner.py` | 烧录封装，接收 SRT 文件路径和样式参数 |
| `FFmpegWrapper.burn_subtitles()` | `srt_maker/video/ffmpeg_wrapper.py` | SRT→ASS 转换 + FFmpeg 烧录，已处理 Windows 路径问题 |
| `StylePanel` | `srt_maker/ui/style_panel.py` | 字体、大小、颜色控件，`get_style()` 返回 dict |
| 菜单/工具栏按钮 | `srt_maker/ui/main_window.py` | "烧录字幕" 动作已绑定到 `_burn_subtitles()` |

## 需要新增/修改

### 1. `BurnWorker` — 烧录后台工作器

**文件:** `srt_maker/ui/burn_worker.py`（新建）

与 `RecognitionWorker` 对称的 QObject worker：

```python
class BurnWorker(QObject):
    progress = Signal(str, int)      # (文本, 百分比)
    finished = Signal()
    error = Signal(str)

    def burn(self, video_path: str, srt_path: str, output_path: str, style: dict):
        """在后台线程执行烧录"""
```

- 信号定义与 `RecognitionWorker` 一致
- `burn()` 槽函数调用 `SubtitleBurner.burn()`
- 烧录过程中发送 `progress("烧录中...", 0)` 表示进行中
- 完成后发送 `finished()`，失败发送 `error(message)`

### 2. `_burn_subtitles()` — 主窗口烧录方法

**文件:** `srt_maker/ui/main_window.py`

替换当前 TODO 占位为完整流程：

1. **前置检查**（已有）：视频已加载 + 字幕已加载
2. **FFmpeg 可用性检查**：与 `_start_recognition` 一致，不可用时弹窗提示
3. **写入临时 SRT 文件**：用 `write_srt(self._subtitles.entries)` 写入临时文件
4. **获取样式**：`self.style_panel.get_style()` → 转换 `QColor` 为 FFmpeg 颜色格式
5. **选择输出路径**：`QFileDialog.getSaveFileName()`，默认文件名与源视频同名加 `_with_subtitles` 后缀
6. **创建 worker + 线程**：`BurnWorker` + `QThread`，连接信号后启动
7. **UI 状态**：显示进度条（不定长模式），禁用烧录按钮

### 3. 颜色格式转换

`QColor` → FFmpeg ASS 颜色格式 `&H00RRGGBB`：

```python
def _qcolor_to_ffmpeg_color(color: QColor) -> str:
    """QColor 转 FFmpeg 颜色格式 &H00RRGGBB"""
    return f"&H00{color.blue():02X}{color.green():02X}{color.red():02X}"
```

FFmpeg 的 ASS 颜色使用 BGR 字节序（与 RGB 相反），`&H00` 前缀表示无透明度。

### 4. 信号处理

- `_on_burn_finished()`: 隐藏进度条，启用烧录按钮，状态栏显示输出路径，清理 worker
- `_on_burn_error(message)`: 弹窗显示错误，清理 worker
- `_cleanup_burn_worker()`: 与 `_cleanup_worker` 对称的清理逻辑

### 5. 进度反馈

FFmpeg 烧录耗时可能很长（超时 600s）。简化方案：

- 进度条设为不定长模式（`setMaximum(0)`），显示持续动画
- 状态栏显示"烧录中..."
- 烧录完成/失败时恢复进度条

### 6. 临时文件清理

- 临时 SRT 文件在烧录完成后删除（worker 的 `finally` 块中）
- 利用 `tempfile.NamedTemporaryFile(delete=False)` 创建，烧录完毕后 `os.unlink`

## 数据流

```
用户点击"烧录字幕"
  → 前置检查（视频 + 字幕 + FFmpeg）
  → write_srt() → 临时 SRT 文件
  → QFileDialog → 输出路径
  → BurnWorker.burn() 在 QThread 中执行
    → SubtitleBurner.burn()
      → FFmpegWrapper.burn_subtitles()
        → SRT → 临时 ASS 文件
        → FFmpeg 烧录
        → 清理 ASS 文件
  → 清理临时 SRT 文件
  → finished/error 信号 → UI 更新
```

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `srt_maker/ui/burn_worker.py` | 新建 | BurnWorker 类 |
| `srt_maker/ui/main_window.py` | 修改 | 完善 `_burn_subtitles()`，新增 `_on_burn_finished`、`_on_burn_error`、`_cleanup_burn_worker` |
| `tests/ui/test_burn_worker.py` | 新建 | BurnWorker 集成测试 |

## 不在本次范围

- 烧录预览（用户确认不需要）
- FFmpeg 进度解析（简化为不定长进度条）
- 批量烧录
