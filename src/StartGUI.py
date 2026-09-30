# -*- coding: utf-8 -*-
"""图片格式转换器 · 图形界面版（含中英文切换）

功能：
    - 批量导入图片或整个文件夹（支持递归、保留目录结构）
    - 转换为 JPG / PNG / WebP / GIF / BMP / TIFF / ICO / PDF
    - 缩放、旋转、翻转、质量调节、透明区域填充背景色
    - 后台线程转换，界面不卡顿，可随时取消
    - 支持把文件直接拖到 exe 图标上启动（命令行参数）
    - 自动检测系统语言（中文 → 中文界面，其他 → 英文界面），并在右上角提供切换按钮

运行：python StartGUI.py
打包：python build_exe.py
"""

from __future__ import annotations

import os
import locale
import queue
import shutil
import sys
import threading
import time

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageFile, ImageOps, ImageTk

ImageFile.LOAD_TRUNCATED_IMAGES = True

APP_TITLE = "图片格式转换器 · 图形界面版"

# 可识别的输入格式
INPUT_EXTS = {
    ".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".webp", ".bmp",
    ".tif", ".tiff", ".ico", ".heic", ".heif", ".avif", ".ppm", ".pgm",
    ".pbm", ".pnm", ".tga", ".dds", ".pcx", ".jp2", ".j2k", ".eps",
}

# 目标格式：name 显示的、fmt Pillow 使用的、ext 输出扩展名、desc 双语描述
TARGETS = [
    {"name": "JPG / JPEG", "fmt": "JPEG", "ext": ".jpg",
     "desc": {"zh": "通用压缩图，照片首选，体积小", "en": "Compact photo format, small size"}},
    {"name": "PNG", "fmt": "PNG", "ext": ".png",
     "desc": {"zh": "透明背景、无损清晰，图标 / 截图常用", "en": "Lossless with transparency, icons / screenshots"}},
    {"name": "WebP", "fmt": "WEBP", "ext": ".webp",
     "desc": {"zh": "谷歌高效格式，体积更小，网页常用", "en": "Efficient Google format, great for web"}},
    {"name": "GIF", "fmt": "GIF", "ext": ".gif",
     "desc": {"zh": "动图 / 表情包，颜色数量有限", "en": "Animated images / emojis, limited colors"}},
    {"name": "BMP", "fmt": "BMP", "ext": ".bmp",
     "desc": {"zh": "无压缩原图，体积很大", "en": "Uncompressed raw bitmap, large size"}},
    {"name": "TIFF", "fmt": "TIFF", "ext": ".tiff",
     "desc": {"zh": "印刷级高清图，设计与出版使用", "en": "Print-grade high resolution for publishing"}},
    {"name": "ICO", "fmt": "ICO", "ext": ".ico",
     "desc": {"zh": "Windows 图标，自动内嵌多尺寸", "en": "Windows icon with embedded sizes"}},
    {"name": "PDF", "fmt": "PDF", "ext": ".pdf",
     "desc": {"zh": "把图片输出为 PDF 文档", "en": "Export the image as a PDF document"}},
]
TARGET_BY_NAME = {item["name"]: item for item in TARGETS}
TARGET_NAMES = [item["name"] for item in TARGETS]

# 旋转 / 翻转选项：内部值固定，显示文案随语言切换
ROTATE_OPTIONS = [
    (0, {"zh": "不旋转", "en": "No rotation"}),
    (90, {"zh": "顺时针 90°", "en": "Rotate 90° CW"}),
    (180, {"zh": "旋转 180°", "en": "Rotate 180°"}),
    (270, {"zh": "顺时针 270°", "en": "Rotate 270° CW"}),
]
FLIP_OPTIONS = [
    ("none", {"zh": "不翻转", "en": "No flip"}),
    ("horizontal", {"zh": "水平翻转", "en": "Flip horizontal"}),
    ("vertical", {"zh": "垂直翻转", "en": "Flip vertical"}),
]

DEFAULT_QUALITY = 88
DEFAULT_BG = "#FFFFFF"

COLOR_BG = "#f4f6fb"
COLOR_PANEL = "#ffffff"
COLOR_ACCENT = "#2f6feb"
COLOR_OK = "#137333"
COLOR_FAIL = "#c5221f"
COLOR_BUSY = "#1a73e8"
COLOR_MUTED = "#5f6b7a"


# --------------------------------------------------------------------------- #
# 多语言
# --------------------------------------------------------------------------- #
# 每个 key 对应 {"zh": ..., "en": ...}。未命中时回退英文，再回退 key 本身。
STR = {
    "app_title":       {"zh": "图片格式转换器 · 图形界面版", "en": "Image Format Converter · GUI"},
    "subtitle":        {"zh": "批量转换图片格式，支持缩放 / 旋转 / 质量调节，全部在本地完成",
                        "en": "Batch convert images with resize / rotate / quality, all local"},

    "add_files":       {"zh": "添加图片", "en": "Add Images"},
    "add_folder":      {"zh": "添加文件夹", "en": "Add Folder"},
    "remove_selected":  {"zh": "移除选中", "en": "Remove Selected"},
    "clear_list":      {"zh": "清空列表", "en": "Clear List"},
    "count":           {"zh": "共 {} 张图片", "en": "Total {} images"},

    "list_title":      {"zh": "待转换图片", "en": "Images to convert"},
    "col_name":        {"zh": "文件名", "en": "File Name"},
    "col_dim":         {"zh": "尺寸", "en": "Dimensions"},
    "col_size":        {"zh": "大小", "en": "Size"},
    "col_status":      {"zh": "状态", "en": "Status"},

    "preview_hint":    {"zh": "选中图片后显示预览", "en": "Preview appears after selection"},
    "preview_no_image": {"zh": "无法预览该图片", "en": "Cannot preview this image"},

    "settings_title":   {"zh": "输出设置", "en": "Output Settings"},
    "target_format":    {"zh": "目标格式", "en": "Target Format"},
    "quality":         {"zh": "画质", "en": "Quality"},
    "size":            {"zh": "尺寸", "en": "Size"},
    "original":        {"zh": "原始", "en": "Original"},
    "keep_ratio":      {"zh": "保持宽高比（填满给定范围，不拉伸）", "en": "Keep aspect ratio (fill, no stretch)"},
    "transform":       {"zh": "旋转 / 翻转", "en": "Rotate / Flip"},
    "background":       {"zh": "背景色", "en": "Background"},
    "transparent_fill": {"zh": "透明区域填充", "en": "Fill for transparent areas"},
    "output_dir":      {"zh": "输出目录", "en": "Output Directory"},
    "browse":          {"zh": "浏览", "en": "Browse"},
    "keep_structure":  {"zh": "保留原有目录结构", "en": "Keep original folder structure"},
    "overwrite":       {"zh": "覆盖同名文件（否则自动改名）", "en": "Overwrite same-name files (else auto-rename)"},

    "ready":           {"zh": "准备就绪", "en": "Ready"},

    "start":           {"zh": "开始转换", "en": "Start"},
    "cancel":          {"zh": "取消", "en": "Cancel"},
    "open_output":     {"zh": "打开输出目录", "en": "Open Output Folder"},

    "status_pending":   {"zh": "待转换", "en": "Pending"},
    "status_waiting":   {"zh": "等待中", "en": "Waiting"},
    "status_busy":      {"zh": "转换中…", "en": "Converting…"},
    "status_done":       {"zh": "完成", "en": "Done"},
    "status_failed":     {"zh": "失败", "en": "Failed"},
    "status_skipped":    {"zh": "跳过", "en": "Skipped"},

    "info_title":        {"zh": "提示", "en": "Note"},
    "no_images_in_folder": {"zh": "该文件夹里没有找到可识别的图片。", "en": "No recognizable images found in this folder."},
    "please_add":       {"zh": "请先添加需要转换的图片。", "en": "Please add images to convert first."},
    "config_error_title": {"zh": "设置错误", "en": "Configuration Error"},
    "pick_format":       {"zh": "请选择目标格式。", "en": "Please select a target format."},
    "width":            {"zh": "宽度", "en": "Width"},
    "height":           {"zh": "高度", "en": "Height"},
    "must_be_number":    {"zh": "{} 必须是数字。", "en": "{} must be a number."},
    "must_be_positive":  {"zh": "{} 必须大于 0。", "en": "{} must be greater than 0."},
    "too_large":        {"zh": "{} 过大（上限 20000）。", "en": "{} is too large (max 20000)."},
    "fill_output":       {"zh": "请填写输出目录。", "en": "Please specify an output directory."},
    "cannot_create_dir": {"zh": "无法创建输出目录", "en": "Cannot create output directory"},
    "output_not_exist":  {"zh": "输出目录还不存在，先执行一次转换吧。", "en": "Output folder does not exist yet. Run a conversion first."},
    "still_running_title": {"zh": "仍在转换", "en": "Conversion in progress"},
    "still_running":     {"zh": "还有图片正在转换，确定要退出吗？", "en": "Images are still converting. Quit anyway?"},

    "dlg_add_files":   {"zh": "选择图片（可多选）", "en": "Select images (multiple)"},
    "dlg_add_folder":   {"zh": "选择包含图片的文件夹", "en": "Select a folder containing images"},
    "dlg_output":       {"zh": "选择输出目录", "en": "Select output directory"},
    "dlg_color":        {"zh": "选择透明区域的填充颜色", "en": "Choose fill color for transparent areas"},
    "img_files":         {"zh": "图片文件", "en": "Image files"},
    "all_files":         {"zh": "所有文件", "en": "All files"},

    "added":            {"zh": "已加入 {} 张图片，共 {} 张待转换。", "en": "Added {} images, {} pending in total."},
    "target_log":       {"zh": "目标格式：{} → {}", "en": "Target format: {} → {}"},
    "skip_same":        {"zh": "与源文件相同，已跳过", "en": "Same as source, skipped"},
    "log_ok":           {"zh": "完成", "en": "OK"},
    "log_fail":         {"zh": "失败", "en": "FAILED"},
    "log_skip":        {"zh": "跳过", "en": "SKIP"},
    "processing":       {"zh": "正在处理 {} / {}：{}", "en": "Processing {} / {}: {}"},
    "cancelled":        {"zh": "已取消", "en": "Cancelled"},
    "done":            {"zh": "转换完成", "en": "Done"},
    "summary":          {"zh": "成功 {} 张，失败 {} 张，跳过 {} 张（共 {} 张）", "en": "Succeeded {}, failed {}, skipped {} (total {})"},
    "summary_time":     {"zh": "，用时 {:.1f} 秒", "en": ", took {:.1f}s"},
    "output_log":       {"zh": "输出目录：{}", "en": "Output: {}"},

    "frames":           {"zh": "帧", "en": " frames"},
}


def _s(key: str, lang: str) -> str:
    """按 key + 当前语言取文案；未命中回退英文，再回退 key 本身。"""
    entry = STR.get(key)
    if not isinstance(entry, dict):
        return key
    return entry.get(lang, entry.get("en", key))


def detect_language() -> str:
    """检测系统语言：中文返回 'zh'，其他返回 'en'。

    优先级：环境变量 IMGCONV_LANG > Windows UI 语言 > locale > 默认英文。
    """
    env = os.environ.get("IMGCONV_LANG", "").strip().lower()
    if env in ("zh", "cn", "zh-cn", "zh_cn", "chinese", "中文"):
        return "zh"
    if env in ("en", "eng", "english", "us", "en-us"):
        return "en"

    # Windows：读取用户默认 UI 语言（比 locale 更准，能反映「显示语言」设置）
    if sys.platform == "win32":
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            primary = lang_id & 0xFF
            if primary == 0x04:      # 0x04 = 中文（简/繁主语言id相同）
                return "zh"
            if primary == 0x09:      # 0x09 = 英文
                return "en"
        except Exception:
            pass

    # 其他平台 / 兜底：locale 与 LANG/LANGUAGE 环境变量
    try:
        loc = (locale.getdefaultlocale()[0] or "").lower()
    except Exception:
        loc = ""
    if not loc:
        loc = (os.environ.get("LANG") or os.environ.get("LANGUAGE") or "").lower()
    if loc.startswith("zh"):
        return "zh"
    return "en"


DEFAULT_LANG = detect_language()


# --------------------------------------------------------------------------- #
# 通用工具
# --------------------------------------------------------------------------- #
def app_dir() -> str:
    """返回输出目录的基准位置。

    打包运行时取 exe 所在目录；源码放在 src/ 里运行时取上一级（项目根目录），
    这样默认输出目录始终是项目根目录下的 output/。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here).lower() == "src":
        return os.path.dirname(here)
    return here


def human_size(num_bytes: float) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def resample_filter():
    return getattr(Image, "Resampling", Image).LANCZOS


def has_alpha(img: Image.Image) -> bool:
    if img.mode in ("RGBA", "LA", "PA"):
        return True
    if img.mode == "P" and "transparency" in img.info:
        return True
    return False


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = (value or DEFAULT_BG).strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return (255, 255, 255)


def is_image_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in INPUT_EXTS


def collect_images(folder: str):
    """递归收集文件夹中的图片，返回 (绝对路径, 相对文件夹的目录) 列表。"""
    found = []
    for root, _dirs, files in os.walk(folder):
        for name in sorted(files):
            if is_image_file(name):
                full = os.path.join(root, name)
                rel = os.path.relpath(root, folder)
                found.append((full, "" if rel == "." else rel))
    return found


# --------------------------------------------------------------------------- #
# 图像处理核心
# --------------------------------------------------------------------------- #
def flatten_alpha(img: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    """把透明通道合成到纯色背景上，返回 RGB 图像。"""
    rgba = img.convert("RGBA")
    base = Image.new("RGB", rgba.size, background)
    base.paste(rgba, (0, 0), rgba.getchannel("A"))
    return base


def apply_transforms(img: Image.Image, opt: dict) -> Image.Image:
    angle = int(opt.get("rotate") or 0)
    if angle:
        transpose = getattr(Image, "Transpose", Image)
        mapping = {
            90: transpose.ROTATE_270,   # 顺时针 90°
            180: transpose.ROTATE_180,
            270: transpose.ROTATE_90,   # 顺时针 270°
        }
        if angle in mapping:
            img = img.transpose(mapping[angle])

    flip = opt.get("flip") or "none"
    if flip != "none":
        transpose = getattr(Image, "Transpose", Image)
        if flip == "horizontal":
            img = img.transpose(transpose.FLIP_LEFT_RIGHT)
        elif flip == "vertical":
            img = img.transpose(transpose.FLIP_TOP_BOTTOM)

    target_w = opt.get("width")
    target_h = opt.get("height")
    if target_w or target_h:
        width, height = img.size
        new_w, new_h = target_w, target_h
        if new_w and new_h:
            if opt.get("keep_ratio"):
                scale = min(new_w / width, new_h / height)
                new_w, new_h = max(1, round(width * scale)), max(1, round(height * scale))
        elif new_w:
            new_h = max(1, round(height * new_w / width))
        else:
            new_w = max(1, round(width * new_h / height))
        if (new_w, new_h) != (width, height):
            img = img.resize((int(new_w), int(new_h)), resample_filter())
    return img


def prepare_frame(img: Image.Image, opt: dict) -> Image.Image:
    """修正手机拍照方向后，应用缩放 / 旋转 / 翻转。"""
    fixed = None
    try:
        fixed = ImageOps.exif_transpose(img)
    except Exception:
        fixed = None
    frame = (fixed if fixed is not None else img).copy()
    if frame.mode == "P":
        frame = frame.convert("RGBA" if "transparency" in img.info else "RGB")
    return apply_transforms(frame, opt)


def to_gif_frame(img: Image.Image):
    """转换为 GIF 所需的调色板图像，返回 (图像, 透明色索引或 None)。"""
    if has_alpha(img):
        rgba = img.convert("RGBA")
        alpha = rgba.getchannel("A")
        paletted = rgba.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
        mask = alpha.point(lambda a: 255 if a <= 128 else 0)
        paletted.paste(255, mask)
        return paletted, 255
    return img.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=256), None


def save_ico(img: Image.Image, path: str) -> None:
    """保存为 ico，必要时补透明边使其成为正方形。"""
    icon = img.convert("RGBA")
    side = max(icon.size)
    if icon.width != icon.height:
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(icon, ((side - icon.width) // 2, (side - icon.height) // 2), icon)
        icon = canvas
    sizes = [(s, s) for s in (256, 128, 64, 48, 32, 16) if s <= side]
    if not sizes:
        sizes = [(max(16, min(side, 256)),) * 2]
    icon.save(path, "ICO", sizes=sizes)


def convert_one(src_path: str, dst_path: str, target: dict, opt: dict) -> None:
    """转换单张图片，失败时抛出异常。"""
    fmt = target["fmt"]
    out_dir = os.path.dirname(dst_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    quality = int(opt.get("quality", DEFAULT_QUALITY))
    background = opt.get("background", hex_to_rgb(DEFAULT_BG))

    with Image.open(src_path) as img:
        frame_count = int(getattr(img, "n_frames", 1) or 1)
        animated = frame_count > 1 and fmt in ("GIF", "WEBP")
        duration = img.info.get("duration", 100) or 100
        loop = img.info.get("loop", 0) or 0
        source_animated_gif = frame_count > 1 and fmt == "GIF"

        if animated:
            frames = []
            for index in range(frame_count):
                img.seek(index)
                frames.append(prepare_frame(img, opt))
        else:
            if frame_count > 1:
                img.seek(0)
            frames = [prepare_frame(img, opt)]

    if fmt == "JPEG":
        page = flatten_alpha(frames[0], background)
        page.save(dst_path, "JPEG", quality=quality, optimize=True,
                  progressive=True, subsampling=0)
    elif fmt == "PNG":
        page = frames[0]
        if not has_alpha(page) and page.mode not in ("RGB", "L"):
            page = page.convert("RGB")
        page.save(dst_path, "PNG", optimize=True, compress_level=6)
    elif fmt == "WEBP":
        if animated:
            frames[0].save(dst_path, "WEBP", save_all=True, append_images=frames[1:],
                           duration=duration, loop=loop, quality=quality, method=4)
        else:
            page = frames[0]
            if page.mode not in ("RGB", "RGBA", "L"):
                page = page.convert("RGBA" if has_alpha(page) else "RGB")
            page.save(dst_path, "WEBP", quality=quality, method=4)
    elif fmt == "GIF":
        gif_frames = []
        transparency = None
        for frame in frames:
            paletted, trans = to_gif_frame(frame)
            gif_frames.append(paletted)
            if trans is not None:
                transparency = trans
        extra = {"transparency": transparency} if transparency is not None else {}
        if source_animated_gif and frame_count > 1:
            gif_frames[0].save(dst_path, "GIF", save_all=True,
                               append_images=gif_frames[1:], duration=duration,
                               loop=loop, optimize=True, disposal=2, **extra)
        else:
            gif_frames[0].save(dst_path, "GIF", optimize=True, **extra)
    elif fmt == "BMP":
        flatten_alpha(frames[0], background).save(dst_path, "BMP")
    elif fmt == "TIFF":
        page = frames[0]
        if not has_alpha(page) and page.mode not in ("RGB", "L"):
            page = page.convert("RGB")
        page.save(dst_path, "TIFF", compression="tiff_deflate")
    elif fmt == "ICO":
        save_ico(frames[0], dst_path)
    elif fmt == "PDF":
        flatten_alpha(frames[0], background).save(dst_path, "PDF", resolution=150.0)
    else:  # pragma: no cover - 目标格式固定
        raise ValueError(f"暂不支持的目标格式: {fmt}")


def unique_path(path: str, used: set, overwrite: bool) -> str:
    """避免覆盖已有文件 / 同批次重名。"""
    folder, filename = os.path.split(path)
    stem, ext = os.path.splitext(filename)
    candidate = path
    index = 1
    while candidate.lower() in used or (not overwrite and os.path.exists(candidate)):
        candidate = os.path.join(folder, f"{stem}_{index}{ext}")
        index += 1
    used.add(candidate.lower())
    return candidate


# --------------------------------------------------------------------------- #
# 界面
# --------------------------------------------------------------------------- #
class ImageConverterApp(tk.Tk):
    def __init__(self, initial_paths=()):
        super().__init__(className="ImageFormatConverter")
        self.title(APP_TITLE)
        self.minsize(1000, 660)
        self.configure(bg=COLOR_BG)

        # 语言：启动时按系统语言；切换按钮在会话内即时改变
        self.lang = DEFAULT_LANG
        self.T = lambda key: _s(key, self.lang)
        self._i18n_regs = []  # 需要在语言切换时刷新文本的控件回调

        self.items = []          # [{"path": 绝对路径, "rel": 相对目录}]
        self.row_ids = {}        # 小写路径 -> treeview iid
        self.iid_paths = {}      # treeview iid -> 绝对路径
        self.preview_photo = None
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker = None
        self.running = False
        self.total = 0
        self.done = 0
        self.ok_count = 0
        self.fail_count = 0
        self.skip_count = 0

        self._setup_style()
        self._build_ui()
        self._apply_language()
        self._bind_shortcuts()
        self._fit_on_screen()

        if initial_paths:
            self.add_paths(list(initial_paths))
        self.after(120, self._poll_events)

    # ---------------- 语言相关 ----------------
    def _reg(self, fn) -> None:
        """注册一个「语言切换时刷新文本」的回调。"""
        self._i18n_regs.append(fn)

    def _tl(self, parent, key, style="Panel.TLabel", **grid_kw):
        """创建带翻译的 Label，并登记刷新。"""
        lbl = ttk.Label(parent, text=self.T(key), style=style)
        self._reg(lambda: lbl.configure(text=self.T(key)))
        if grid_kw:
            lbl.grid(**grid_kw)
        return lbl

    def _tbtn(self, parent, key, command, **pack_kw):
        """创建带翻译的 Button，并登记刷新。"""
        btn = ttk.Button(parent, text=self.T(key), command=command)
        self._reg(lambda: btn.configure(text=self.T(key)))
        if pack_kw:
            btn.pack(**pack_kw)
        return btn

    def _opt_value(self, options, label):
        for value, labels in options:
            if labels.get(self.lang) == label or labels.get("en") == label:
                return value
        return options[0][0]

    def _opt_label(self, options, value):
        for val, labels in options:
            if val == value:
                return labels.get(self.lang, labels.get("en", ""))
        return options[0][1].get(self.lang, "")

    def _current_format_desc(self) -> str:
        target = TARGET_BY_NAME.get(self.format_var.get())
        if target:
            return target["desc"][self.lang]
        return ""

    def _refresh_rotate_flip(self) -> None:
        cur_rot = self._opt_value(ROTATE_OPTIONS, self.rotate_var.get())
        cur_flip = self._opt_value(FLIP_OPTIONS, self.flip_var.get())
        self.rotate_box["values"] = [lbl[self.lang] for _, lbl in ROTATE_OPTIONS]
        self.flip_box["values"] = [lbl[self.lang] for _, lbl in FLIP_OPTIONS]
        self.rotate_var.set(self._opt_label(ROTATE_OPTIONS, cur_rot))
        self.flip_var.set(self._opt_label(FLIP_OPTIONS, cur_flip))

    def _apply_language(self) -> None:
        """刷新所有可见文案到当前语言。"""
        self.title(self.T("app_title"))
        for fn in self._i18n_regs:
            fn()
        # 表格列头
        self.tree.heading("name", text=self.T("col_name"))
        self.tree.heading("dim", text=self.T("col_dim"))
        self.tree.heading("size", text=self.T("col_size"))
        self.tree.heading("status", text=self.T("col_status"))
        # 目标格式描述
        self.format_desc.configure(text=self._current_format_desc())
        # 旋转 / 翻转下拉
        self._refresh_rotate_flip()
        # 计数与状态
        self._refresh_counts()
        if not self.running:
            self.status_label.configure(text=self.T("ready"))
        # 预览提示
        if self.preview_photo is None:
            self.preview_label.configure(text=self.T("preview_hint"))
        # 切换按钮：显示「点击后将切换到的语言」
        self.lang_btn.configure(text="EN" if self.lang == "zh" else "中文")

    def on_toggle_lang(self) -> None:
        self.lang = "en" if self.lang == "zh" else "zh"
        self._apply_language()

    # ---------------- 外观 ----------------
    def _setup_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

        family = "Microsoft YaHei UI"
        self.dpi_scale = 1.0
        try:
            self.dpi_scale = max(1.0, self.winfo_fpixels("1i") / 96.0)
            self.tk.call("tk", "scaling", max(1.0, self.winfo_fpixels("1i") / 72.0))
        except Exception:
            pass
        scale = self.dpi_scale

        for font_name in ("TkDefaultFont", "TkTextFont", "TkMenuFont",
                          "TkHeadingFont", "TkCaptionFont", "TkTooltipFont"):
            try:
                from tkinter import font as tkfont
                tkfont.nametofont(font_name).configure(family=family, size=10)
            except Exception:
                pass
        self.option_add("*Font", (family, 10))

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure("TLabel", background=COLOR_BG, foreground="#1f2933")
        style.configure("Panel.TLabel", background=COLOR_PANEL)
        style.configure("Title.TLabel", background=COLOR_BG, foreground="#12203a",
                        font=(family, 17, "bold"))
        style.configure("Sub.TLabel", background=COLOR_BG, foreground=COLOR_MUTED,
                        font=(family, 9))
        style.configure("Head.TLabel", background=COLOR_BG, font=(family, 10, "bold"))
        style.configure("Muted.TLabel", background=COLOR_BG, foreground=COLOR_MUTED,
                        font=(family, 9))
        style.configure("Accent.TButton", font=(family, 11, "bold"), padding=(18, 8))
        style.configure("TButton", padding=(10, 5))
        style.configure("Treeview", rowheight=int(24 * scale), background=COLOR_PANEL,
                        fieldbackground=COLOR_PANEL)
        style.configure("Treeview.Heading", font=(family, 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#1f5fd8")])
        style.configure("TLabelframe", background=COLOR_PANEL)
        style.configure("TLabelframe.Label", background=COLOR_PANEL,
                        foreground="#12203a", font=(family, 10, "bold"))
        style.configure("TCheckbutton", background=COLOR_PANEL)
        style.configure("Progress.Horizontal.TProgressbar", thickness=14)

    def _fit_on_screen(self) -> None:
        """按内容需求 + 屏幕分辨率（含高 DPI 缩放）决定窗口大小并居中。"""
        self.update_idletasks()
        scale = max(1.0, self.winfo_fpixels("1i") / 96.0)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        min_w, min_h = int(880 * scale), int(560 * scale)
        max_w, max_h = int(screen_w * 0.92), int(screen_h * 0.90)
        width = max(min_w, min(self.winfo_reqwidth() + 20, max_w))
        height = max(min_h, min(self.winfo_reqheight() + 20, max_h))
        width = min(width, max_w)
        height = min(height, max_h)
        self.minsize(min(min_w, width), min(min_h, height))

        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ---------------- 布局 ----------------
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=3)
        self.rowconfigure(4, weight=1)

        # ---- 顶部标题栏（含语言切换按钮）----
        header = ttk.Frame(self, padding=(16, 12, 16, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        self.title_label = ttk.Label(header, text=self.T("app_title"), style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")
        self._reg(lambda: self.title_label.configure(text=self.T("app_title")))

        self.sub_label = ttk.Label(header, text=self.T("subtitle"), style="Sub.TLabel")
        self.sub_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self._reg(lambda: self.sub_label.configure(text=self.T("subtitle")))

        lang_frame = ttk.Frame(header, padding=(0, 0))
        lang_frame.grid(row=0, column=1, rowspan=2, sticky="ne")
        self.lang_btn = ttk.Button(lang_frame, text="EN", width=6,
                                  command=self.on_toggle_lang, takefocus=False)
        self.lang_btn.pack()

        # ---- 工具栏 ----
        toolbar = ttk.Frame(self, padding=(16, 0, 16, 8))
        toolbar.grid(row=1, column=0, sticky="ew")
        self._tbtn(toolbar, "add_files", self.on_add_files, side="left")
        self._tbtn(toolbar, "add_folder", self.on_add_folder, side="left", padx=6)
        self._tbtn(toolbar, "remove_selected", self.on_remove_selected, side="left")
        self._tbtn(toolbar, "clear_list", self.on_clear, side="left", padx=6)
        self.count_label = ttk.Label(toolbar, text="", style="Muted.TLabel")
        self.count_label.pack(side="right")

        # ---- 主体 ----
        body = ttk.Frame(self, padding=(16, 0, 16, 0))
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        list_panel = ttk.Frame(body, style="Panel.TFrame", padding=1)
        list_panel.grid(row=0, column=0, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        self.list_title_label = ttk.Label(list_panel, text=self.T("list_title"),
                                        style="Panel.TLabel",
                                        font=("Microsoft YaHei UI", 10, "bold"))
        self.list_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))
        self._reg(lambda: self.list_title_label.configure(text=self.T("list_title")))

        columns = ("name", "dim", "size", "status")
        self.tree = ttk.Treeview(list_panel, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("name", text=self.T("col_name"))
        self.tree.heading("dim", text=self.T("col_dim"))
        self.tree.heading("size", text=self.T("col_size"))
        self.tree.heading("status", text=self.T("col_status"))
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("dim", width=130, anchor="center", stretch=False)
        self.tree.column("size", width=100, anchor="e", stretch=False)
        self.tree.column("status", width=110, anchor="center", stretch=False)
        self.tree.tag_configure("ok", foreground=COLOR_OK)
        self.tree.tag_configure("fail", foreground=COLOR_FAIL)
        self.tree.tag_configure("busy", foreground=COLOR_BUSY)
        self.tree.tag_configure("skip", foreground=COLOR_MUTED)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=1, column=1, sticky="ns", pady=(0, 8))

        # ---- 右侧设置 + 预览 ----
        side = ttk.Frame(body, style="Panel.TFrame", padding=(12, 10, 12, 10))
        side.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        side.columnconfigure(0, weight=1)

        self.preview_width = int(260 * self.dpi_scale)
        self.preview_height = int(170 * self.dpi_scale)
        self.preview_box = tk.Frame(side, bg="#e9edf5", width=self.preview_width,
                                   height=self.preview_height, highlightthickness=1,
                                   highlightbackground="#d3dae6")
        self.preview_box.grid(row=0, column=0, sticky="ew")
        self.preview_box.grid_propagate(False)
        self.preview_label = tk.Label(self.preview_box, text=self.T("preview_hint"),
                                    bg="#e9edf5", fg=COLOR_MUTED)
        self.preview_label.place(relx=0.5, rely=0.5, anchor="center")
        self.preview_info = ttk.Label(side, text="—", style="Panel.TLabel",
                                     foreground=COLOR_MUTED, justify="center")
        self.preview_info.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self._reg(lambda: self.preview_info.configure(text="—"))

        self._build_settings(side)

        # ---- 进度条 ----
        progress = ttk.Frame(self, padding=(16, 10, 16, 0))
        progress.grid(row=3, column=0, sticky="ew")
        progress.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(progress, style="Progress.Horizontal.TProgressbar",
                                       mode="determinate", maximum=100, value=0)
        self.progress.grid(row=0, column=0, sticky="ew")
        self.status_label = ttk.Label(progress, text=self.T("ready"), style="Muted.TLabel")
        self.status_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # ---- 日志 ----
        log = ttk.Frame(self, padding=(16, 8, 16, 0))
        log.grid(row=4, column=0, sticky="nsew")
        log.columnconfigure(0, weight=1)
        log.rowconfigure(0, weight=1)
        self.log = tk.Text(log, height=5, wrap="none", relief="solid", borderwidth=1,
                           bg="#0f172a", fg="#d7e3f4", insertbackground="#d7e3f4",
                           font=("Consolas", 9), state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        log_scroll.grid(row=0, column=1, sticky="ns")

        # ---- 底部操作栏 ----
        footer = ttk.Frame(self, padding=(16, 10, 16, 14))
        footer.grid(row=5, column=0, sticky="ew")
        self.start_button = ttk.Button(footer, text=self.T("start"), style="Accent.TButton",
                                     command=self.on_start)
        self.start_button.pack(side="left")
        self._reg(lambda: self.start_button.configure(text=self.T("start")))
        self.cancel_button = ttk.Button(footer, text=self.T("cancel"), command=self.on_cancel,
                                      state="disabled")
        self.cancel_button.pack(side="left", padx=8)
        self._reg(lambda: self.cancel_button.configure(text=self.T("cancel")))
        self._tbtn(footer, "open_output", self.on_open_output, side="left")
        self.total_label = ttk.Label(footer, text="", style="Muted.TLabel")
        self.total_label.pack(side="right")

    def _build_settings(self, parent) -> None:
        box = ttk.Labelframe(parent, text=self.T("settings_title"), padding=(12, 8, 12, 12))
        box.grid(row=2, column=0, sticky="ew")
        box.columnconfigure(1, weight=1, minsize=int(150 * self.dpi_scale))
        row = 0

        self._tl(box, "target_format", row=row, column=0, sticky="w", pady=3)
        self.format_var = tk.StringVar(value=TARGETS[0]["name"])
        self.format_box = ttk.Combobox(box, textvariable=self.format_var, values=TARGET_NAMES,
                                      state="readonly", width=16)
        self.format_box.grid(row=row, column=1, sticky="ew", pady=3)
        self.format_box.bind("<<ComboboxSelected>>", self.on_format_change)
        row += 1

        self.format_desc = ttk.Label(box, text=self._current_format_desc(), style="Muted.TLabel",
                                    wraplength=250, justify="left")
        self.format_desc.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))
        self._reg(lambda: self.format_desc.configure(text=self._current_format_desc()))
        row += 1

        self._tl(box, "quality", row=row, column=0, sticky="w")
        quality_wrap = ttk.Frame(box, style="Panel.TFrame")
        quality_wrap.grid(row=row, column=1, sticky="ew")
        quality_wrap.columnconfigure(0, weight=1)
        self.quality_var = tk.DoubleVar(value=DEFAULT_QUALITY)
        self.quality_scale = ttk.Scale(quality_wrap, from_=1, to=100, orient="horizontal",
                                      variable=self.quality_var, command=self.on_quality_change)
        self.quality_scale.grid(row=0, column=0, sticky="ew")
        self.quality_label = ttk.Label(quality_wrap, text=str(DEFAULT_QUALITY), width=4,
                                      style="Panel.TLabel")
        self.quality_label.grid(row=0, column=1, sticky="e")
        row += 1

        self._tl(box, "size", row=row, column=0, sticky="w", pady=(4, 0))
        size_wrap = ttk.Frame(box, style="Panel.TFrame")
        size_wrap.grid(row=row, column=1, sticky="ew", pady=(4, 0))
        self.width_var = tk.StringVar(value="")
        self.height_var = tk.StringVar(value="")
        ttk.Entry(size_wrap, textvariable=self.width_var, width=6).grid(row=0, column=0)
        ttk.Label(size_wrap, text="×", style="Panel.TLabel").grid(row=0, column=1, padx=3)
        ttk.Entry(size_wrap, textvariable=self.height_var, width=6).grid(row=0, column=2)
        self.orig_btn = ttk.Button(size_wrap, text=self.T("original"), width=5,
                                  command=lambda: (self.width_var.set(""), self.height_var.set("")))
        self.orig_btn.grid(row=0, column=3, padx=(6, 0))
        self._reg(lambda: self.orig_btn.configure(text=self.T("original")))
        row += 1

        self.keep_ratio_var = tk.BooleanVar(value=True)
        self.keep_ratio_chk = ttk.Checkbutton(box, text=self.T("keep_ratio"),
                                            variable=self.keep_ratio_var)
        self.keep_ratio_chk.grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self._reg(lambda: self.keep_ratio_chk.configure(text=self.T("keep_ratio")))
        row += 1

        self._tl(box, "transform", row=row, column=0, sticky="w", pady=(6, 0))
        transform_wrap = ttk.Frame(box, style="Panel.TFrame")
        transform_wrap.grid(row=row, column=1, sticky="w", pady=(6, 0))
        self.rotate_var = tk.StringVar(value=self._opt_label(ROTATE_OPTIONS, 0))
        self.rotate_box = ttk.Combobox(transform_wrap, textvariable=self.rotate_var,
                                      values=[lbl[self.lang] for _, lbl in ROTATE_OPTIONS],
                                      state="readonly", width=8)
        self.rotate_box.grid(row=0, column=0, sticky="w")
        self.flip_var = tk.StringVar(value=self._opt_label(FLIP_OPTIONS, "none"))
        self.flip_box = ttk.Combobox(transform_wrap, textvariable=self.flip_var,
                                    values=[lbl[self.lang] for _, lbl in FLIP_OPTIONS],
                                    state="readonly", width=8)
        self.flip_box.grid(row=0, column=1, sticky="w", padx=(4, 0))
        row += 1

        self._tl(box, "background", row=row, column=0, sticky="w", pady=(4, 0))
        bg_wrap = ttk.Frame(box, style="Panel.TFrame")
        bg_wrap.grid(row=row, column=1, sticky="w", pady=(4, 0))
        self.background_var = tk.StringVar(value=DEFAULT_BG)
        self.bg_swatch = tk.Button(bg_wrap, text=DEFAULT_BG, width=8, relief="groove",
                                  bg=DEFAULT_BG, command=self.on_pick_color)
        self.bg_swatch.grid(row=0, column=0)
        self._tl(bg_wrap, "transparent_fill", style="Muted.TLabel").grid(row=0, column=1,
                                                                       padx=(6, 0))
        row += 1

        ttk.Separator(box, orient="horizontal").grid(row=row, column=0, columnspan=2,
                                                  sticky="ew", pady=8)
        row += 1

        self._tl(box, "output_dir", row=row, column=0, sticky="w")
        out_wrap = ttk.Frame(box, style="Panel.TFrame")
        out_wrap.grid(row=row, column=1, sticky="ew")
        out_wrap.columnconfigure(0, weight=1)
        self.output_var = tk.StringVar(value=os.path.join(app_dir(), "output"))
        ttk.Entry(out_wrap, textvariable=self.output_var).grid(row=0, column=0, sticky="ew")
        self.browse_btn = ttk.Button(out_wrap, text=self.T("browse"), width=5,
                                    command=self.on_pick_output)
        self.browse_btn.grid(row=0, column=1, padx=(4, 0))
        self._reg(lambda: self.browse_btn.configure(text=self.T("browse")))
        row += 1

        self.keep_structure_var = tk.BooleanVar(value=True)
        self.keep_structure_chk = ttk.Checkbutton(box, text=self.T("keep_structure"),
                                                variable=self.keep_structure_var)
        self.keep_structure_chk.grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self._reg(lambda: self.keep_structure_chk.configure(text=self.T("keep_structure")))
        row += 1

        self.overwrite_var = tk.BooleanVar(value=True)
        self.overwrite_chk = ttk.Checkbutton(box, text=self.T("overwrite"),
                                            variable=self.overwrite_var)
        self.overwrite_chk.grid(row=row, column=0, columnspan=2, sticky="w")
        self._reg(lambda: self.overwrite_chk.configure(text=self.T("overwrite")))

    def _bind_shortcuts(self) -> None:
        self.bind("<Delete>", lambda _e: self.on_remove_selected())
        self.bind("<Control-o>", lambda _e: self.on_add_files())
        self.bind("<Control-O>", lambda _e: self.on_add_files())
        self.bind("<Return>", lambda _e: self.on_start())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- 列表操作 ----------------
    def add_paths(self, paths) -> int:
        added = 0
        known = {item["path"].lower() for item in self.items}
        collected = []
        for raw in paths:
            if not raw:
                continue
            path = os.path.abspath(raw)
            if os.path.isdir(path):
                collected.extend(collect_images(path))
            elif os.path.isfile(path):
                collected.append((path, ""))
        for path, rel in collected:
            key = path.lower()
            if key in known:
                continue
            known.add(key)
            info = self._describe(path)
            self.items.append({"path": path, "rel": rel, "info": info})
            item_id = self.tree.insert("", "end", values=(os.path.basename(path), info["dim"],
                                                        info["size"], self.T("status_pending")))
            self.row_ids[key] = item_id
            self.iid_paths[item_id] = path
            added += 1
        if added:
            self._refresh_counts()
            self.log_line(self.T("added").format(added, len(self.items)))
            if not self.tree.selection():
                first = self.tree.get_children()
                if first:
                    self.tree.selection_set(first[0])
                    self.tree.focus(first[0])
                    self.on_select()
        return added

    def _describe(self, path: str) -> dict:
        info = {"dim": "—", "size": human_size(os.path.getsize(path))}
        try:
            with Image.open(path) as img:
                frames = int(getattr(img, "n_frames", 1) or 1)
                dim = f"{img.width}×{img.height}"
                if frames > 1:
                    dim += f" ({frames}{self.T('frames')})"
                info["dim"] = dim
                info["mode"] = img.mode
                info["frames"] = frames
        except Exception:
            info["mode"] = "未知"
            info["frames"] = 1
        return info

    def _refresh_counts(self) -> None:
        self.count_label.configure(text=self.T("count").format(len(self.items)))

    def on_add_files(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in sorted(INPUT_EXTS))
        paths = filedialog.askopenfilenames(
            title=self.T("dlg_add_files"),
            filetypes=[(self.T("img_files"), patterns), (self.T("all_files"), "*.*")])
        if paths:
            self.add_paths(list(paths))

    def on_add_folder(self) -> None:
        folder = filedialog.askdirectory(title=self.T("dlg_add_folder"))
        if folder:
            count = self.add_paths([folder])
            if count == 0:
                messagebox.showinfo(self.T("info_title"), self.T("no_images_in_folder"))

    def on_remove_selected(self) -> None:
        if self.running:
            return
        selection = self.tree.selection()
        if not selection:
            return
        for item_id in selection:
            self.tree.delete(item_id)
            path = self.iid_paths.pop(item_id, None)
            if path:
                key = path.lower()
                self.row_ids.pop(key, None)
                self.items = [item for item in self.items if item["path"].lower() != key]
        self._refresh_counts()

    def on_clear(self) -> None:
        if self.running:
            return
        self.tree.delete(*self.tree.get_children())
        self.items.clear()
        self.row_ids.clear()
        self.iid_paths.clear()
        self.preview_photo = None
        self.preview_label.configure(image="", text=self.T("preview_hint"))
        self.preview_info.configure(text="—")
        self._refresh_counts()
        self.progress.configure(value=0)
        self.status_label.configure(text=self.T("ready"))
        self.total_label.configure(text="")

    def on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        path = self.iid_paths.get(item_id)
        if not path:
            return
        for item in self.items:
            if item["path"] == path:
                self._show_preview(item)
                break

    def _show_preview(self, item: dict) -> None:
        path = item["path"]
        box_w = max(120, self.preview_box.winfo_width() or self.preview_width)
        box_h = max(90, self.preview_box.winfo_height() or self.preview_height)
        try:
            with Image.open(path) as img:
                frames = int(getattr(img, "n_frames", 1) or 1)
                mode = img.mode
                size = img.size
                fixed = ImageOps.exif_transpose(img) or img
                thumb = fixed.copy()
                thumb.thumbnail((box_w - 12, box_h - 12), resample_filter())
        except Exception as exc:
            self.preview_photo = None
            self.preview_label.configure(image="", text=self.T("preview_no_image"))
            self.preview_info.configure(text=str(exc)[:80])
            return

        self.preview_photo = ImageTk.PhotoImage(thumb)
        self.preview_label.configure(image=self.preview_photo, text="")
        detail = f"{size[0]} × {size[1]} · {mode}"
        if frames > 1:
            detail += f" · {frames}{self.T('frames')}"
        detail += f" · {human_size(os.path.getsize(path))}"
        self.preview_info.configure(text=detail)

    # ---------------- 设置交互 ----------------
    def on_format_change(self, _event=None) -> None:
        self.format_desc.configure(text=self._current_format_desc())
        self.quality_scale.state(["!disabled"] if self.format_var.get() in
                                 ("JPG / JPEG", "WebP") else ["disabled"])

    def on_quality_change(self, value) -> None:
        self.quality_label.configure(text=str(int(float(value))))

    def on_pick_color(self) -> None:
        color = colorchooser.askcolor(color=self.background_var.get(),
                                     title=self.T("dlg_color"))
        if color and color[1]:
            self.background_var.set(color[1].upper())
            self.bg_swatch.configure(bg=color[1], activebackground=color[1],
                                    text=color[1].upper())

    def on_pick_output(self) -> None:
        folder = filedialog.askdirectory(title=self.T("dlg_output"),
                                        initialdir=self.output_var.get() or app_dir())
        if folder:
            self.output_var.set(folder)

    def on_open_output(self) -> None:
        folder = self.output_var.get().strip() or os.path.join(app_dir(), "output")
        if not os.path.isdir(folder):
            messagebox.showinfo(self.T("info_title"), self.T("output_not_exist"))
            return
        try:
            os.startfile(folder)  # type: ignore[attr-defined]
        except Exception:
            messagebox.showinfo(self.T("output_dir"), folder)

    def collect_options(self):
        target = TARGET_BY_NAME.get(self.format_var.get())
        if target is None:
            messagebox.showerror(self.T("config_error_title"), self.T("pick_format"))
            return None

        def parse(entry_value, label):
            text = (entry_value or "").strip()
            if not text:
                return None
            try:
                number = int(float(text))
            except ValueError:
                raise ValueError(self.T("must_be_number").format(label))
            if number <= 0:
                raise ValueError(self.T("must_be_positive").format(label))
            if number > 20000:
                raise ValueError(self.T("too_large").format(label))
            return number

        try:
            width = parse(self.width_var.get(), self.T("width"))
            height = parse(self.height_var.get(), self.T("height"))
        except ValueError as exc:
            messagebox.showerror(self.T("config_error_title"), str(exc))
            return None

        out_dir = self.output_var.get().strip()
        if not out_dir:
            messagebox.showerror(self.T("config_error_title"), self.T("fill_output"))
            return None

        return {
            "target": target,
            "quality": int(round(self.quality_var.get())),
            "width": width,
            "height": height,
            "keep_ratio": bool(self.keep_ratio_var.get()),
            "rotate": self._opt_value(ROTATE_OPTIONS, self.rotate_var.get()),
            "flip": self._opt_value(FLIP_OPTIONS, self.flip_var.get()),
            "background": hex_to_rgb(self.background_var.get()),
            "out_dir": out_dir,
            "keep_structure": bool(self.keep_structure_var.get()),
            "overwrite": bool(self.overwrite_var.get()),
        }

    # ---------------- 转换流程 ----------------
    def on_start(self) -> None:
        if self.running:
            return
        if not self.items:
            messagebox.showinfo(self.T("info_title"), self.T("please_add"))
            return
        opt = self.collect_options()
        if opt is None:
            return
        try:
            os.makedirs(opt["out_dir"], exist_ok=True)
        except OSError as exc:
            messagebox.showerror(self.T("cannot_create_dir"), str(exc))
            return

        self.cancel_event.clear()
        self.running = True
        self.done = self.ok_count = self.fail_count = self.skip_count = 0
        self.total = len(self.items)
        self.progress.configure(maximum=max(1, self.total), value=0)
        self.total_label.configure(text=f"0 / {self.total}")
        self.status_label.configure(text=self.T("status_busy"))
        self._set_busy(True)
        self._clear_log()
        self.log_line(self.T("target_log").format(opt['target']['name'], opt['out_dir']))

        for item in self.items:
            item_id = self.row_ids.get(item["path"].lower())
            if item_id:
                self.tree.set(item_id, "status", self.T("status_waiting"))
                self.tree.item(item_id, tags=())

        snapshot = [dict(item) for item in self.items]
        self.worker = threading.Thread(target=self._work, args=(snapshot, opt), daemon=True)
        self.worker.start()

    def _work(self, files, opt) -> None:
        started = time.time()
        used = set()
        for index, item in enumerate(files, 1):
            if self.cancel_event.is_set():
                self.events.put(("cancelled", index - 1, len(files)))
                return
            src = item["path"]
            target = opt["target"]
            key = src.lower()
            self.events.put(("begin", key, index, len(files), src))

            rel_dir = item.get("rel", "") if opt["keep_structure"] else ""
            out_dir = os.path.join(opt["out_dir"], rel_dir) if rel_dir else opt["out_dir"]
            stem = os.path.splitext(os.path.basename(src))[0]
            dst = os.path.join(out_dir, stem + target["ext"])

            if os.path.abspath(dst).lower() == os.path.abspath(src).lower():
                self.events.put(("skip", key, self.T("skip_same")))
                continue
            try:
                dst = unique_path(dst, used, opt["overwrite"])
            except OSError as exc:
                self.events.put(("fail", key, f"{type(exc).__name__}: {exc}"))
                continue

            begin = time.time()
            try:
                convert_one(src, dst, target, opt)
                detail = f"{human_size(os.path.getsize(dst))} · {time.time() - begin:.2f}s"
                self.events.put(("success", key, detail, dst))
            except Exception as exc:  # noqa: BLE001 - 单张失败不影响其他文件
                self.events.put(("fail", key, f"{type(exc).__name__}: {exc}"))
        self.events.put(("finished", len(files), time.time() - started))

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(120, self._poll_events)

    def _handle_event(self, event) -> None:
        kind = event[0]
        if kind == "begin":
            _, key, index, total, src = event
            item_id = self.row_ids.get(key)
            if item_id:
                self.tree.set(item_id, "status", self.T("status_busy"))
                self.tree.item(item_id, tags=("busy",))
                self.tree.see(item_id)
            self.status_label.configure(
                text=self.T("processing").format(index, total, os.path.basename(src)))
        elif kind == "success":
            _, key, detail, dst = event
            item_id = self.row_ids.get(key)
            if item_id:
                self.tree.set(item_id, "status", self.T("status_done"))
                self.tree.item(item_id, tags=("ok",))
            self.ok_count += 1
            self.done += 1
            self.log_line(f"{self.T('log_ok')} {os.path.basename(dst)}  ({detail})")
            self._update_progress()
        elif kind == "fail":
            _, key, message = event
            item_id = self.row_ids.get(key)
            if item_id:
                self.tree.set(item_id, "status", self.T("status_failed"))
                self.tree.item(item_id, tags=("fail",))
            self.fail_count += 1
            self.done += 1
            self.log_line(f"{self.T('log_fail')} {message}")
            self._update_progress()
        elif kind == "skip":
            _, key, message = event
            item_id = self.row_ids.get(key)
            if item_id:
                self.tree.set(item_id, "status", self.T("status_skipped"))
                self.tree.item(item_id, tags=("skip",))
            self.skip_count += 1
            self.done += 1
            self.log_line(f"{self.T('log_skip')} {message}")
            self._update_progress()
        elif kind == "finished":
            _, total, seconds = event
            self._finish(total, seconds, cancelled=False)
        elif kind == "cancelled":
            _, done, total = event
            self._finish(total, 0.0, cancelled=True)

    def _update_progress(self) -> None:
        self.progress.configure(value=self.done)
        self.total_label.configure(text=f"{self.done} / {self.total}")

    def _finish(self, total: int, seconds: float, cancelled: bool) -> None:
        self.running = False
        self._set_busy(False)
        headline = self.T("cancelled") if cancelled else self.T("done")
        summary = (self.T("summary").format(self.ok_count, self.fail_count,
                                           self.skip_count, total))
        if seconds:
            summary += self.T("summary_time").format(seconds)
        self.status_label.configure(text=summary)
        self.log_line("")
        self.log_line(summary)
        self.log_line(self.T("output_log").format(self.output_var.get()))

    def _set_busy(self, busy: bool) -> None:
        self.start_button.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")

    def on_cancel(self) -> None:
        if self.running:
            self.cancel_event.set()
            self.status_label.configure(text=self.T("status_busy"))

    # ---------------- 日志 ----------------
    def log_line(self, text: str) -> None:
        if not self.winfo_exists():
            return
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def on_close(self) -> None:
        if self.running:
            if not messagebox.askyesno(self.T("still_running_title"), self.T("still_running")):
                return
            self.cancel_event.set()
        self.destroy()


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
    except Exception:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def run_selftest(report_path: str) -> int:
    """无界面自检：依次转换为所有目标格式，把结果写入文本文件。

    打包后可用 `StartGUI.exe --selftest` 验证 exe 是否完整可用。
    """
    import tempfile

    from PIL import ImageDraw

    work = tempfile.mkdtemp(prefix="imgtool_selftest_")
    lines = [f"自检时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", f"临时目录：{work}", ""]
    failures = 0
    try:
        rgb_path = os.path.join(work, "sample.jpg")
        rgb = Image.new("RGB", (320, 200), (30, 90, 200))
        ImageDraw.Draw(rgb).ellipse((40, 40, 200, 160), fill=(240, 200, 40))
        rgb.save(rgb_path, quality=92)

        rgba_path = os.path.join(work, "logo.png")
        rgba = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        ImageDraw.Draw(rgba).ellipse((8, 8, 120, 120), fill=(255, 0, 0, 255))
        rgba.save(rgba_path)

        frames = []
        for index in range(3):
            frame = Image.new("RGB", (64, 64), (0, 0, 0))
            ImageDraw.Draw(frame).rectangle((index * 18, 0, index * 18 + 20, 64),
                                           fill=(60 + index * 60, 30, 200 - index * 50))
            frames.append(frame)
        anim_path = os.path.join(work, "anim.gif")
        frames[0].save(anim_path, save_all=True, append_images=frames[1:], duration=100, loop=0)

        options = {"quality": 88, "width": 100, "height": 100, "keep_ratio": True,
                   "rotate": 90, "flip": "horizontal", "background": (255, 255, 255)}
        for source in (rgb_path, rgba_path, anim_path):
            for target in TARGETS:
                dst = os.path.join(work, "out",
                                   os.path.splitext(os.path.basename(source))[0] + target["ext"])
                try:
                    convert_one(source, dst, target, dict(options))
                    size = os.path.getsize(dst)
                    with open(dst, "rb") as handle:
                        head = handle.read(8)
                    if size <= 0:
                        raise ValueError("输出文件为空")
                    lines.append(f"OK   {os.path.basename(source):<10} -> "
                                 f"{os.path.basename(dst):<14} {size:>8} 字节  {head[:4]!r}")
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    lines.append(f"FAIL {os.path.basename(source):<10} -> "
                                 f"{target['name']}：{type(exc).__name__}: {exc}")

        lines.append("")
        lines.append("自检结果：全部通过" if failures == 0 else f"自检结果：{failures} 项失败")
    except Exception as exc:  # noqa: BLE001
        failures += 1
        lines.append(f"自检异常：{type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    text = "\n".join(lines)
    try:
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    except OSError:
        pass
    print(text)
    return 1 if failures else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest(os.path.join(app_dir(), "selftest_report.txt"))
    enable_dpi_awareness()
    initial = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    app = ImageConverterApp(initial)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
