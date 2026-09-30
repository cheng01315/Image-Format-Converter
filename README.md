# 图片格式转换器

[English](README.en.md) | 简体中文

一个轻量的图片格式转换工具，提供图形界面，支持批量转换与常用图片处理。

## 功能特点

- **多格式支持**：在 JPG/JPEG、PNG、WebP、GIF、BMP、TIFF、ICO、PDF 之间转换
- **批量转换**：一次导入多张图片或整个文件夹，自动递归子目录
- **常用图片处理**：按宽高缩放、旋转、水平/垂直翻转、调节画质
- **透明处理**：转成 JPG/BMP/PDF 时可指定透明区域的填充背景色
- **动图保留**：GIF/WebP 动图转换后仍是动图（保留帧与播放速度）
- **保持目录结构**：转换结果按原目录层级输出
- **后台执行**：转换过程不卡界面，可随时取消，逐张显示成功/失败
- **开箱即用**：Windows 下双击 exe 即可运行，无需安装 Python

## 使用方法

1. 直接使用项目根目录的 `StartGUI.exe`
2. 双击运行 `StartGUI.exe`
3. 点击「添加图片」或「添加文件夹」导入需要处理的图片（也可以直接把图片拖到 exe 图标上启动）
4. 在右侧选择目标格式、画质、尺寸、旋转 / 翻转、输出目录等选项
5. 点击「开始转换」，完成后点击「打开输出目录」查看结果

输出的默认目录是 exe 同级的 `output` 文件夹（首次转换时自动创建）。

## 支持的格式

| 格式 | 描述 | 最佳用途 |
|--------|-------------|----------|
| JPG/JPEG | 通用压缩图，体积小 | 照片首选 |
| PNG | 透明背景、无损清晰 | 图标、截图 |
| WebP | 谷歌高效格式，体积更小 | 网页多用 |
| GIF | 动图，色彩少 | 表情包、简单动画 |
| BMP | 无压缩原图，体积超大 | 高质量打印 |
| TIFF | 印刷高清图 | 专业设计/出版 |
| ICO | Windows 图标，内嵌多尺寸 | 程序图标 |
| PDF | 图片转 PDF 文档 | 归档、分享 |

## 从源码运行

```bash
# 安装依赖
pip install Pillow

python src/StartGUI.py
```

## 打包成 exe

```bash
pip install Pillow pyinstaller
python src/build_exe.py
```

脚本会自动生成图标 `app.ico` 并调用 PyInstaller，产物为 `dist/StartGUI.exe`，同时复制一份到项目根目录。
打包后的 exe 支持自检：

```bash
StartGUI.exe --selftest
```

会在 exe 同级目录生成 `selftest_report.txt`，逐一验证所有格式的转换结果。

## 项目结构

```
image-format-converter/
├── StartGUI.exe        # 图形界面版可执行文件（Windows，免安装）
├── README.md           # 中文文档
├── README.en.md        # 英文文档
├── LICENSE             # GNU General Public License v2
├── src/                # 全部源码
│   ├── StartGUI.py     # 图形界面版（tkinter + Pillow）
│   └── build_exe.py    # 打包脚本（生成图标 + 调用 PyInstaller）
└── output/             # 转换结果输出目录（首次转换自动创建）
```

## 需求要求

- Python 3.8+（运行源码时）
- [Pillow](https://pypi.org/project/Pillow/)（`pip install Pillow`）
- [PyInstaller](https://pypi.org/project/pyinstaller/)（仅打包时需要）
- Windows 系统（预编译可执行文件）

图形界面使用 Python 标准库 tkinter，无需额外安装 GUI 依赖。

## 文档

- 中文文档（当前页面）：[README.md](README.md)
- English documentation: [README.en.md](README.en.md)

## 贡献

欢迎贡献！欢迎提交 issues 或 pull requests。

## 许可证

本项目基于 [GNU General Public License v2](LICENSE) 发布。
