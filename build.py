#!/usr/bin/env python3
"""SRT Maker 构建脚本

自动化流程：
1. 检查 Python 版本
2. 下载 FFmpeg 静态编译版本
3. 运行 PyInstaller 打包
4. 复制 FFmpeg 到打包输出目录
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
FFMPEG_BUILD_DIR = PROJECT_ROOT / "build" / "ffmpeg"
DIST_DIR = PROJECT_ROOT / "dist" / "srt_maker"
FFMPEG_URL = (
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full-full.7z"
)

def check_python_version() -> bool:
    """检查 Python 版本 >= 3.10"""
    if sys.version_info < (3, 10):
        print("错误: 需要 Python 3.10 或更高版本")
        return False
    print(f"Python 版本: {sys.version}")
    return True

def download_ffmpeg() -> Path:
    """下载 FFmpeg 静态编译版本

    使用 FFmpeg 的 gyan.dev 预编译版本。
    由于 7z 格式需要解压工具，这里使用 requests 下载并处理。

    返回 FFmpeg 可执行文件所在目录。
    """
    if (FFMPEG_BUILD_DIR / "ffmpeg.exe").exists():
        print("FFmpeg 已存在，跳过下载")
        return FFMPEG_BUILD_DIR

    print("正在下载 FFmpeg...")
    FFMPEG_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import requests

        # 尝试下载 gyan.dev 的 7z 包
        print(f"下载: {FFMPEG_URL}")
        response = requests.get(FFMPEG_URL, stream=True, timeout=300)
        response.raise_for_status()

        archive_path = FFMPEG_BUILD_DIR / "ffmpeg.7z"
        with open(archive_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("正在解压 FFmpeg...")
        # 尝试使用 7z 解压
        try:
            subprocess.run(
                ["7z", "x", str(archive_path), f"-o{FFMPEG_BUILD_DIR}", "-y"],
                check=True,
                timeout=120,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            # 尝试使用 Python 的 py7zr
            try:
                import py7zr
                with py7zr.SevenZipFile(archive_path, "r") as archive:
                    archive.extractall(FFMPEG_BUILD_DIR)
            except ImportError:
                print("警告: 无法解压 7z 文件。请手动下载 FFmpeg 并放到 build/ffmpeg/ 目录")
                print("下载地址: https://www.gyan.dev/ffmpeg/builds/")
                raise

        archive_path.unlink()

        # 查找 ffmpeg.exe — gyan.dev 的目录结构为 ffmpeg-*/bin/
        ffmpeg_exe = list(FFMPEG_BUILD_DIR.glob("**/ffmpeg.exe"))
        if ffmpeg_exe:
            # 如果解压到子目录，将可执行文件移到顶层
            for exe in ffmpeg_exe:
                if exe.parent != FFMPEG_BUILD_DIR:
                    shutil.move(str(exe), FFMPEG_BUILD_DIR / exe.name)

        if (FFMPEG_BUILD_DIR / "ffmpeg.exe").exists():
            print("FFmpeg 下载完成")
            return FFMPEG_BUILD_DIR
        else:
            print("警告: 未找到 ffmpeg.exe，请手动放置")
            return FFMPEG_BUILD_DIR

    except Exception as e:
        print(f"下载 FFmpeg 失败: {e}")
        print("请手动下载 FFmpeg 并放到 build/ffmpeg/ 目录")
        print("下载地址: https://www.gyan.dev/ffmpeg/builds/")
        return FFMPEG_BUILD_DIR

def run_pyinstaller() -> bool:
    """运行 PyInstaller 打包"""
    print("正在运行 PyInstaller...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "srt_maker.spec", "--clean"],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print("PyInstaller 打包失败")
        return False
    print("PyInstaller 打包完成")
    return True

def copy_ffmpeg_to_dist() -> bool:
    """将 FFmpeg 复制到打包输出目录"""
    ffmpeg_exe = FFMPEG_BUILD_DIR / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        print("警告: build/ffmpeg/ffmpeg.exe 不存在，跳过复制")
        return False

    dist_ffmpeg = DIST_DIR / "ffmpeg"
    dist_ffmpeg.mkdir(exist_ok=True)

    for exe in ["ffmpeg.exe", "ffprobe.exe"]:
        src = FFMPEG_BUILD_DIR / exe
        dst = dist_ffmpeg / exe
        if src.exists():
            shutil.copy2(src, dst)
            print(f"已复制: {exe}")

    return True

def main():
    print("=" * 50)
    print("SRT Maker 构建脚本")
    print("=" * 50)

    # 1. 检查 Python 版本
    if not check_python_version():
        sys.exit(1)

    # 2. 下载 FFmpeg
    download_ffmpeg()

    # 3. 运行 PyInstaller
    if not run_pyinstaller():
        sys.exit(1)

    # 4. 复制 FFmpeg
    copy_ffmpeg_to_dist()

    print()
    print("=" * 50)
    print("构建完成!")
    print(f"输出目录: {DIST_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
