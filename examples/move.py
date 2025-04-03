import os
import shutil
from pathlib import Path
from typing import List

def get_all_files(source_dir: str) -> List[Path]:
    """获取目录下所有文件的路径"""
    files = []
    source_path = Path(source_dir)
    for item in source_path.rglob('*'):
        if item.is_file():
            files.append(item)
    return files

def get_unique_filename(target_dir: str, filename: str) -> str:
    """生成唯一的文件名，如果存在重复则添加数字后缀"""
    base_path = os.path.join(target_dir, filename)
    if not os.path.exists(base_path):
        return base_path
    
    name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def move_files(source_dir: str, target_dir: str) -> None:
    """移动文件到目标目录"""
    # 确保目标目录存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # 获取所有文件
    files = get_all_files(source_dir)
    total_files = len(files)
    
    if total_files == 0:
        print("没有找到需要移动的文件")
        return
    
    print(f"找到 {total_files} 个文件需要移动")
    
    # 移动文件
    for i, file_path in enumerate(files, 1):
        try:
            # 获取相对于源目录的文件名
            rel_path = file_path.relative_to(Path(source_dir))
            # 如果文件在子目录中，只获取文件名
            filename = rel_path.name
            
            # 获取唯一的目标文件路径
            target_path = get_unique_filename(target_dir, filename)
            
            # 移动文件
            shutil.move(str(file_path), target_path)
            
            # 显示进度
            print(f"[{i}/{total_files}] 已移动: {filename} -> {os.path.basename(target_path)}")
            
        except Exception as e:
            print(f"移动文件 {file_path} 时出错: {str(e)}")

def main():
    # 获取用户输入
    source_dir = input("请输入源目录路径: ").strip()
    target_dir = input("请输入目标目录路径: ").strip()
    
    # 如果输入的是相对路径，转换为绝对路径
    if not os.path.isabs(source_dir):
        source_dir = os.path.abspath(source_dir)
    if not os.path.isabs(target_dir):
        target_dir = os.path.abspath(target_dir)
    
    print(f"\n开始移动文件:")
    print(f"源目录: {source_dir}")
    print(f"目标目录: {target_dir}\n")
    
    # 移动文件
    move_files(source_dir, target_dir)
    print("\n文件移动完成！")

if __name__ == "__main__":
    main()