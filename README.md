# 图片格式转换器

一个简单轻量的图片格式转换工具，支持多种图片格式。

## 功能特点

- **多格式支持**: 支持在 JPG/JPEG、PNG、GIF、WebP、BMP 和 TIFF 之间转换
- **批量转换**: 一次转换多张图片
- **保持目录结构**: 在输出中保留原始文件夹结构
- **跨平台**: 在 Windows 上无需安装 Python 即可运行
- **友好界面**: 简单的命令行界面，附带格式说明

## 支持的格式

| 格式 | 描述 | 最佳用途 |
|--------|-------------|----------|
| JPG/JPEG | 通用压缩图，体积小 | 照片首选 |
| PNG | 透明背景、无损清晰 | 图标、截图 |
| GIF | 动图，色彩少 | 表情包、简单动画 |
| WebP | 谷歌高效格式，体积更小 | 网页多用 |
| BMP | 无压缩原图，体积超大 | 高质量打印 |
| TIFF | 印刷高清图 | 专业设计/出版 |

## 使用方法

### Windows（无需Python）

1. 从 [Releases](https://github.com/yourusername/image-format-converter/releases) 页面下载 `Start.exe`
2. 在 `Start.exe` 同目录下创建 `input` 和 `output` 文件夹
3. 将图片放入 `input` 文件夹
4. 双击 `Start.exe` 运行
5. 按照屏幕提示选择目标格式

### 从源代码运行

```bash
# 安装依赖
pip install Pillow

# 运行程序
python Start.py
```

## 项目结构

```
image-format-converter/
├── Start.exe          # Windows可执行文件 (~14MB)
├── Start.py           # Python源代码
├── input/             # 放入待转换图片
└── output/            # 转换后的图片输出位置
```

## 工作原理

1. 程序扫描 `input` 文件夹中的支持格式图片
2. 显示检测到的格式及其描述
3. 提示用户选择目标格式
4. 转换所有图片并在 `output` 中保留目录结构

## 需求要求

- Python 3.x（运行源代码时）
- Pillow 库 (`pip install Pillow`)
- Windows 系统（预编译可执行文件）

## 许可证

MIT License - 可自由使用和分发。

## 贡献

欢迎贡献！欢迎提交 issues 或 pull requests。
