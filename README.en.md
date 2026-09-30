# Image Format Converter

[简体中文](README.md) | English

A lightweight image format conversion tool with a graphical interface, supporting batch conversion and common image processing.

## Features

- **Multiple formats**: convert between JPG/JPEG, PNG, WebP, GIF, BMP, TIFF, ICO and PDF
- **Batch conversion**: import many images or a whole folder at once, sub-folders are scanned recursively
- **Image processing**: resize by width/height, rotate, flip horizontally/vertically, adjust quality
- **Transparency handling**: pick a background color to fill transparent areas when exporting to JPG/BMP/PDF
- **Animation preserved**: converting an animated GIF/WebP keeps every frame and the original frame delay
- **Directory structure kept**: results mirror the folder layout of the source files
- **Background execution**: the window stays responsive, a running job can be cancelled, and every file reports success or failure
- **Zero setup**: just double-click the exe on Windows, no Python installation required

## Usage

1. Download it from [Releases](https://github.com/cheng01315/Image-Format-Converter/releases), or use `StartGUI.exe` from the repository root
2. Double-click `StartGUI.exe`
3. Use 「添加图片」 (Add images) or 「添加文件夹」 (Add folder) to import your pictures — you can also drag files onto the exe icon to launch it with them
4. Choose the target format, quality, size, rotation / flip and output folder on the right
5. Click 「开始转换」 (Start conversion); when it finishes, 「打开输出目录」 (Open output folder) shows the results

The default output folder is `output`, next to the exe (created automatically on the first conversion).

## Language

The interface is bilingual (Chinese / English) and switches with one click:

- **Auto-detect**: on launch it reads the system display language — Chinese systems default to Chinese, everything else defaults to English.
- **Manual switch**: the **中 / EN** button at the top-right of the window toggles all interface text (menus, buttons, settings, status, logs, …) live, while the app is running.
- **Force a language**: set the environment variable `IMGCONV_LANG` to `zh` or `en` before launching to skip auto-detection and pin the language (handy for testing).

## Supported formats

| Format | Description | Best for |
|--------|-------------|----------|
| JPG/JPEG | Widely used lossy format, small files | Photos |
| PNG | Lossless with transparency | Icons, screenshots |
| WebP | Efficient format from Google, even smaller | Web pages |
| GIF | Animated images with a limited palette | Memes, simple animations |
| BMP | Uncompressed bitmap, very large | High quality printing |
| TIFF | High resolution format | Professional design/publishing |
| ICO | Windows icon with multiple embedded sizes | Application icons |
| PDF | Images written into a PDF document | Archiving, sharing |

## Running from source

```bash
# install dependencies
pip install Pillow

python src/StartGUI.py
```

## Building the executable

```bash
pip install Pillow pyinstaller
python src/build_exe.py
```

The script generates the icon `app.ico` and calls PyInstaller; the result is `dist/StartGUI.exe`, which is also copied to the repository root.
The packaged exe ships with a self test:

```bash
StartGUI.exe --selftest
```

It writes `selftest_report.txt` next to the exe, verifying the conversion result of every supported format.

## Project structure

```
image-format-converter/
├── StartGUI.exe        # graphical version, portable Windows executable
├── README.md           # documentation (Chinese)
├── README.en.md        # documentation (English)
├── LICENSE             # GNU General Public License v2
├── src/                # all source code
│   ├── StartGUI.py     # graphical version (tkinter + Pillow)
│   └── build_exe.py    # build script (icon generation + PyInstaller)
└── output/             # conversion results (created on first conversion)
```

## Requirements

- Python 3.8+ (when running from source)
- [Pillow](https://pypi.org/project/Pillow/) (`pip install Pillow`)
- [PyInstaller](https://pypi.org/project/pyinstaller/) (only needed for building)
- Windows (for the prebuilt executables)

The graphical interface uses tkinter from the Python standard library, so no extra GUI dependency is needed.

## Documentation

- English documentation (this page): [README.en.md](README.en.md)
- 中文文档: [README.md](README.md)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This project is released under the [GNU General Public License v2](LICENSE).
