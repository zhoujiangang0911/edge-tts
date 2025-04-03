import os
import re

def rename_files(folder_path, increment):
    # 获取文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 使用正则匹配文件名中的数字部分
        match = re.match(r"(\d+)-(\d+)(\.\w+)", filename)
        if match:
            num1, num2, ext = match.groups()
            # 计算新的文件名
            new_name = f"{int(num1) + increment}-{int(num2) + increment}{ext}"
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_name)
            
            # 重命名文件
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {new_name}")

# 示例使用
folder_path = "/Volumes/mydata/git/edge-tts/examples/output/srzy/mp3"  # 替换为你的文件夹路径
increment = 336  # 替换为你想要增加的数字
rename_files(folder_path, increment)
