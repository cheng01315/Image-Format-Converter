import os
import sys
from PIL import Image

def get_image_formats_in_folder(folder_path):
    """获取文件夹中所有图片的格式"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg', '.heic'}
    formats_found = set()
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                formats_found.add(ext)
    
    return formats_found

def format_description(ext):
    """返回格式的描述信息"""
    descriptions = {
        '.jpg': 'JPG/JPEG - 通用压缩图，照片首选，体积小',
        '.jpeg': 'JPG/JPEG - 通用压缩图，照片首选，体积小',
        '.png': 'PNG - 透明背景、无损清晰，图标/截图常用',
        '.gif': 'GIF - 动图，色彩少，表情包专用',
        '.webp': 'WebP - 谷歌高效格式，体积更小，网页多用',
        '.bmp': 'BMP - 无压缩原图，体积超大',
        '.tiff': 'TIFF - 印刷高清图，设计出版使用',
        '.svg': 'SVG - 矢量图，放大不失真，logo图标',
        '.heic': 'HEIC - 苹果手机原图格式'
    }
    return descriptions.get(ext, f"{ext} - 未知格式")

def convert_image(input_path, output_path, target_format):
    """转换单张图片"""
    try:
        with Image.open(input_path) as img:
            # 如果是RGBA格式且目标格式不支持透明，转换为RGB
            if img.mode == 'RGBA' and target_format.lower() in ['jpg', 'jpeg', 'bmp']:
                img = img.convert('RGB')
            
            # 保存图片
            img.save(output_path, format=target_format.upper())
            return True
    except Exception as e:
        print(f"  转换失败: {os.path.basename(input_path)} - {str(e)}")
        return False

def main():
    input_folder = 'input'
    output_folder = 'output'
    
    # 确保input和output文件夹存在
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # 扫描input文件夹中的图片格式
    print("正在扫描input文件夹中的图片格式...")
    formats_found = get_image_formats_in_folder(input_folder)
    
    if not formats_found:
        print("在input文件夹中未找到任何图片文件。")
        print("请将图片文件夹放入input目录后再运行程序。")
        input("按回车键退出...")
        return
    
    # 显示找到的格式
    print("\n已识别到以下图片格式：")
    for fmt in sorted(formats_found):
        print(f"  • {format_description(fmt)}")
    
    # 显示可选的目标格式
    print("\n请选择要转换的目标格式：")
    formats = [
        ('1', 'JPG/JPEG', '通用压缩图，照片首选，体积小'),
        ('2', 'PNG', '透明背景、无损清晰，图标/截图常用'),
        ('3', 'GIF', '动图，色彩少，表情包专用'),
        ('4', 'WebP', '谷歌高效格式，体积更小，网页多用'),
        ('5', 'BMP', '无压缩原图，体积超大'),
        ('6', 'TIFF', '印刷高清图，设计出版使用'),
    ]
    
    for key, name, desc in formats:
        print(f"  {key}. {name} - {desc}")
    
    # 获取用户选择
    while True:
        choice = input("\n请输入选择的格式编号（1-6）：")
        if choice in [f[0] for f in formats]:
            target_format = formats[int(choice)-1][1].upper()
            if target_format == 'JPG/JPEG':
                target_format = 'JPEG'
            elif target_format == 'WEBP':
                target_format = 'WebP'
            break
        print("请输入有效的编号（1-6）")
    
    # 开始转换
    print(f"\n开始转换图片为 {target_format} 格式...")
    total_files = 0
    success_count = 0
    failed_count = 0
    
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic'}:
                total_files += 1
                input_path = os.path.join(root, file)
                
                # 保持目录结构
                rel_path = os.path.relpath(root, input_folder)
                output_dir = os.path.join(output_folder, rel_path)
                os.makedirs(output_dir, exist_ok=True)
                
                # 生成输出文件名
                base_name = os.path.splitext(file)[0]
                output_filename = f"{base_name}.{target_format.lower()}"
                output_path = os.path.join(output_dir, output_filename)
                
                print(f"  转换: {file} -> {output_filename}")
                if convert_image(input_path, output_path, target_format):
                    success_count += 1
                else:
                    failed_count += 1
    
    # 输出结果
    print(f"\n转换完成！")
    print(f"  总计: {total_files} 个文件")
    print(f"  成功: {success_count} 个")
    print(f"  失败: {failed_count} 个")
    
    if success_count > 0:
        print(f"\n转换后的图片已保存到: {os.path.abspath(output_folder)}")
    
    input("\n按回车键退出...")

if __name__ == '__main__':
    main()