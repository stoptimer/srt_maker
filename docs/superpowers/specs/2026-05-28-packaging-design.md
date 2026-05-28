# SRT Maker 打包分发设计

## 背景

SRT Maker 需要打包为不依赖任何环境的独立程序，普通 Windows 用户双击即可运行。当前项目依赖 PyTorch、Whisper、PySide6 等重量级库，以及 FFmpeg 外部工具，打包方案需妥善处理这些依赖。

## 方案概述

使用 **PyInstaller 目录模式** 打包，将 Python 运行时、所有依赖库、FFmpeg 工具捆绑到同一目录中。用户无需安装 Python 或任何前置环境。

## 打包结构

```
srt_maker_dist/
├── srt_maker.exe           # 主程序入口
├── _internal/              # PyInstaller 自动生成的依赖目录
│   ├── Python310/          # Python 运行时
│   ├── torch/              # PyTorch
│   ├── whisper/            # Whisper
│   ├── PySide6/            # Qt6
│   └── ...                 # 其他依赖
├── ffmpeg/                 # FFmpeg 可执行文件
│   ├── ffmpeg.exe
│   └── ffprobe.exe
```

## 关键设计决策

### 1. PyInstaller 目录模式 vs 单文件模式

选择**目录模式**而非单文件模式：
- PyTorch 有大量动态加载的 DLL，单文件模式下解压到临时目录时容易找不到依赖
- 目录模式启动快，无需解压
- 便于调试和更新

### 2. FFmpeg 捆绑

- 下载 FFmpeg 静态编译版本（仅 ffmpeg.exe + ffprobe.exe）
- 放入打包目录的 `ffmpeg/` 子目录
- 程序启动时按以下优先级查找 FFmpeg：
  1. 用户配置的 `ffmpeg_dir`（来自 `~/.srt_maker/config.json`）
  2. 打包目录下的 `ffmpeg/` 子目录
  3. 系统 PATH

### 3. Whisper 模型处理

Whisper 模型文件较大（tiny 139MB, base 143MB, small 466MB, medium 1.5GB, large 2.9GB）。采用**按需下载**策略：
- 打包时不捆绑模型文件
- 程序首次使用 Whisper 时，`whisper.load_model()` 会自动从 HuggingFace 下载模型到 `~/.cache/whisper/`
- 网络不可用时给出明确的错误提示

### 4. PyInstaller 隐藏导入

以下库有动态导入，需显式声明：

```
--hidden-import=torch
--hidden-import=whisper
--hidden-import=silero_vad
--hidden-import=pyqtgraph
--hidden-import=opencv_python
--hidden-import=numpy
--hidden-import=ffmpeg
```

### 5. 资源文件处理

PySide6 的资源文件和 Qt 平台插件需要额外处理：
- Qt 平台插件：`--collect-all PySide6`
- 如程序有图标等静态资源，通过 `--add-data` 包含

### 6. 配置文件路径

配置存储在 `~/.srt_maker/config.json`，打包后仍使用此路径，不随程序分发。

## 实现步骤

### 步骤 1: 创建 PyInstaller Spec 文件

生成 `srt_maker.spec`，配置隐藏导入和数据文件收集。

### 步骤 2: 创建构建脚本

创建 `build.py`，自动化以下流程：
1. 检查 Python 版本（>= 3.10）
2. 下载 FFmpeg 静态编译版本到 `build/ffmpeg/`
3. 运行 PyInstaller 打包
4. 将 FFmpeg 复制到打包输出目录

### 步骤 3: 修改 FFmpeg 路径查找逻辑

更新 `FFmpegWrapper` 的 `_ffmpeg_cmd()` 方法，增加对打包目录下 `ffmpeg/` 的查找：

```python
def _bundled_ffmpeg_dir() -> str:
    """获取打包目录下的 FFmpeg 路径"""
    # PyInstaller 打包后的目录
    base = getattr(sys, '_MEIPASS', Path(__file__).parent)
    bundled = Path(base) / "ffmpeg"
    if (bundled / "ffmpeg.exe").exists():
        return str(bundled)
    return ""
```

查找顺序：用户配置 → 打包目录 → 系统 PATH

### 步骤 4: 测试打包结果

在干净的 Windows 环境中验证：
1. 程序能正常启动
2. 音频提取功能正常（依赖 FFmpeg）
3. Whisper 识别功能正常
4. 字幕烧录功能正常

## 验证方式

1. **本地验证**：在开发机上运行打包后的程序，确认所有功能正常
2. **干净环境验证**：在无 Python 环境的 Windows 虚拟机中测试
3. **FFmpeg 路径验证**：删除用户配置，确认程序能使用打包目录下的 FFmpeg
