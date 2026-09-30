# -*- coding: utf-8 -*-
"""把图形界面版打包成单文件 exe。

用法：
    python src/build_exe.py

产物：
    dist/StartGUI.exe   （同时会复制一份到项目根目录）
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))            # 源码目录（src/）
PROJECT_ROOT = os.path.dirname(BASE)                         # 项目根目录
ENTRY = os.path.join(BASE, "StartGUI.py")
ICON_PATH = os.path.join(PROJECT_ROOT, "app.ico")
APP_NAME = "StartGUI"


def log(message: str) -> None:
    print(f"[build] {message}", flush=True)


def make_icon() -> str:
    """用 Pillow 生成一个多尺寸 ico 图标。"""
    from PIL import Image, ImageDraw

    size = 256
    gradient = Image.new("RGB", (size, size))
    pixels = gradient.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2.0 * (size - 1))
            pixels[x, y] = (int(47 + (124 - 47) * t),
                            int(111 + (74 - 111) * t),
                            int(235 + (214 - 235) * t))

    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=56, fill=255)
    icon.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((44, 62, 212, 198), radius=18, outline=(255, 255, 255, 240), width=11)
    draw.ellipse((76, 86, 116, 126), fill=(255, 214, 102, 255))
    draw.polygon([(62, 186), (120, 122), (156, 162), (176, 144), (202, 186)],
                 fill=(255, 255, 255, 240))

    icon.save(ICON_PATH, format="ICO",
              sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    log(f"图标已生成：{ICON_PATH}")
    return ICON_PATH


def locate_tcl():
    """找到 tcl/tk 脚本目录，供 PyInstaller 打包 tkinter 使用。"""
    tcl_lib = os.environ.get("TCL_LIBRARY")
    tk_lib = os.environ.get("TK_LIBRARY")
    if tcl_lib and tk_lib and os.path.isfile(os.path.join(tcl_lib, "init.tcl")):
        return tcl_lib, tk_lib

    candidates = [
        os.path.join(sys.base_prefix, "tcl"),
        os.path.join(os.path.dirname(sys.executable), "tcl"),
        os.path.join(PROJECT_ROOT, ".buildtemp", "tcl"),
    ]
    for root in candidates:
        tcl_lib = os.path.join(root, "tcl8.6")
        tk_lib = os.path.join(root, "tk8.6")
        if os.path.isfile(os.path.join(tcl_lib, "init.tcl")):
            return tcl_lib, tk_lib
    return None, None


def build() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        log("未安装 PyInstaller，请先执行：pip install pyinstaller")
        return 1

    icon = make_icon()
    tcl_lib, tk_lib = locate_tcl()
    env = dict(os.environ)
    if tcl_lib:
        env["TCL_LIBRARY"] = tcl_lib
        env["TK_LIBRARY"] = tk_lib
        log(f"tcl 目录：{tcl_lib}")
    else:
        log("警告：未找到 tcl/tk 目录，tkinter 可能无法打包")

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", APP_NAME,
        "--icon", icon,
        "--distpath", os.path.join(PROJECT_ROOT, "dist"),
        "--workpath", os.path.join(PROJECT_ROOT, "build"),
        "--specpath", os.path.join(PROJECT_ROOT, "build"),
        "--exclude-module", "numpy",
        "--exclude-module", "pytest",
        "--exclude-module", "PIL.ImageQt",
        ENTRY,
    ]
    log("开始打包：" + " ".join(command[1:]))
    result = subprocess.run(command, cwd=PROJECT_ROOT, env=env)
    if result.returncode != 0:
        log("打包失败")
        return result.returncode

    built = os.path.join(PROJECT_ROOT, "dist", APP_NAME + ".exe")
    if not os.path.isfile(built):
        log(f"未找到产物：{built}")
        return 1
    target = os.path.join(PROJECT_ROOT, APP_NAME + ".exe")
    shutil.copy2(built, target)
    size_mb = os.path.getsize(target) / 1024 / 1024
    log(f"完成：{built}")
    log(f"已复制到项目根目录：{target}（{size_mb:.1f} MB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
