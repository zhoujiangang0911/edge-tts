#!/usr/bin/env python3
import os
import re
import argparse
import sys

# 数字到中文的映射
CHINESE_NUMS = {
    0: '零', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五',
    6: '六', 7: '七', 8: '八', 9: '九', 10: '十',
    100: '百', 1000: '千', 10000: '万'
}

# 中文到数字的映射（用于还原功能）
CHINESE_TO_NUM = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000
}

def num_to_chinese(num):
    """将数字转换为中文表示"""
    if num <= 10:
        return CHINESE_NUMS[num]
    elif num < 100:
        if num % 10 == 0:  # 整十数
            return CHINESE_NUMS[10] + ('' if num == 10 else CHINESE_NUMS[num // 10])
        else:
            return ('' if num < 20 else CHINESE_NUMS[num // 10]) + CHINESE_NUMS[10] + ('' if num % 10 == 0 else CHINESE_NUMS[num % 10])
    elif num < 1000:
        hundred = num // 100
        remainder = num % 100
        result = CHINESE_NUMS[hundred] + CHINESE_NUMS[100]
        if remainder == 0:
            return result
        elif remainder < 10:
            return result + CHINESE_NUMS[0] + num_to_chinese(remainder)
        else:
            return result + num_to_chinese(remainder)
    elif num < 10000:
        thousand = num // 1000
        remainder = num % 1000
        result = CHINESE_NUMS[thousand] + CHINESE_NUMS[1000]
        if remainder == 0:
            return result
        elif remainder < 100:
            return result + CHINESE_NUMS[0] + num_to_chinese(remainder)
        else:
            return result + num_to_chinese(remainder)
    else:
        # 处理万及以上的数字
        wan = num // 10000
        remainder = num % 10000
        result = num_to_chinese(wan) + CHINESE_NUMS[10000]
        if remainder == 0:
            return result
        elif remainder < 1000:
            return result + CHINESE_NUMS[0] + num_to_chinese(remainder)
        else:
            return result + num_to_chinese(remainder)

def chinese_to_num(chinese_str):
    """将中文数字转换为阿拉伯数字（简化版，仅支持1-99）"""
    if '十' not in chinese_str:
        return CHINESE_TO_NUM.get(chinese_str, 0)
    elif chinese_str == '十':
        return 10
    elif chinese_str.startswith('十'):
        return 10 + CHINESE_TO_NUM.get(chinese_str[1:], 0)
    else:
        parts = chinese_str.split('十')
        if len(parts) == 2:
            tens = CHINESE_TO_NUM.get(parts[0], 1) * 10
            ones = CHINESE_TO_NUM.get(parts[1], 0) if parts[1] else 0
            return tens + ones
    return 0

def rename_files(folder_path, dry_run=False):
    """重命名文件夹中的文件"""
    if not os.path.isdir(folder_path):
        print(f"错误: {folder_path} 不是一个有效的目录")
        return
    
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    renamed_count = 0
    
    for filename in files:
        # 使用正则匹配文件名中的数字部分
        # 匹配模式1: 1-1.txt 或 1-1.mp3 等 (单章节范围)
        match = re.match(r"(\d+)-(\d+)(\.[\w]+)$", filename)
        if match:
            num1, num2, ext = match.groups()
            num1, num2 = int(num1), int(num2)
            
            # 如果是单章节 (如 1-1.txt)
            if num1 == num2:
                new_name = f"第{num_to_chinese(num1)}章{ext}"
            else:
                # 如果是章节范围 (如 1-3.txt)
                new_name = f"第{num_to_chinese(num1)}章-第{num_to_chinese(num2)}章{ext}"
            
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_name)
            
            # 检查新文件名是否已存在
            if os.path.exists(new_path):
                print(f"警告: 无法重命名 {filename} -> {new_name}, 目标文件已存在")
                continue
            
            # 执行重命名或显示将要执行的操作
            if dry_run:
                print(f"将重命名: {filename} -> {new_name}")
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"已重命名: {filename} -> {new_name}")
                    renamed_count += 1
                except Exception as e:
                    print(f"重命名 {filename} 时出错: {str(e)}")
        else:
            # 匹配模式2: 单纯的数字.txt 或 数字.mp3 等 (如 1.txt)
            match = re.match(r"(\d+)(\.[\w]+)$", filename)
            if match:
                num, ext = match.groups()
                num = int(num)
                new_name = f"第{num_to_chinese(num)}章{ext}"
                
                old_path = os.path.join(folder_path, filename)
                new_path = os.path.join(folder_path, new_name)
                
                # 检查新文件名是否已存在
                if os.path.exists(new_path):
                    print(f"警告: 无法重命名 {filename} -> {new_name}, 目标文件已存在")
                    continue
                
                # 执行重命名或显示将要执行的操作
                if dry_run:
                    print(f"将重命名: {filename} -> {new_name}")
                else:
                    try:
                        os.rename(old_path, new_path)
                        print(f"已重命名: {filename} -> {new_name}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"重命名 {filename} 时出错: {str(e)}")
    
    if dry_run:
        print(f"预览完成，共有 {renamed_count} 个文件将被重命名")
    else:
        print(f"重命名完成，共重命名了 {renamed_count} 个文件")

def restore_files(folder_path, dry_run=False):
    """还原已重命名的文件到原始的数字格式"""
    if not os.path.isdir(folder_path):
        print(f"错误: {folder_path} 不是一个有效的目录")
        return
    
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    restored_count = 0
    
    for filename in files:
        # 匹配模式1: 第X章.ext
        match = re.match(r"第([\u4e00-\u9fa5]+)章(\.[\w]+)$", filename)
        if match:
            chinese_num, ext = match.groups()
            try:
                num = chinese_to_num(chinese_num)
                new_name = f"{num}-{num}{ext}"
                
                old_path = os.path.join(folder_path, filename)
                new_path = os.path.join(folder_path, new_name)
                
                # 检查新文件名是否已存在
                if os.path.exists(new_path):
                    print(f"警告: 无法还原 {filename} -> {new_name}, 目标文件已存在")
                    continue
                
                # 执行重命名或显示将要执行的操作
                if dry_run:
                    print(f"将还原: {filename} -> {new_name}")
                else:
                    try:
                        os.rename(old_path, new_path)
                        print(f"已还原: {filename} -> {new_name}")
                        restored_count += 1
                    except Exception as e:
                        print(f"还原 {filename} 时出错: {str(e)}")
            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")
                continue
        
        # 匹配模式2: 第X章-第Y章.ext
        match = re.match(r"第([\u4e00-\u9fa5]+)章-第([\u4e00-\u9fa5]+)章(\.[\w]+)$", filename)
        if match:
            chinese_num1, chinese_num2, ext = match.groups()
            try:
                num1 = chinese_to_num(chinese_num1)
                num2 = chinese_to_num(chinese_num2)
                new_name = f"{num1}-{num2}{ext}"
                
                old_path = os.path.join(folder_path, filename)
                new_path = os.path.join(folder_path, new_name)
                
                # 检查新文件名是否已存在
                if os.path.exists(new_path):
                    print(f"警告: 无法还原 {filename} -> {new_name}, 目标文件已存在")
                    continue
                
                # 执行重命名或显示将要执行的操作
                if dry_run:
                    print(f"将还原: {filename} -> {new_name}")
                else:
                    try:
                        os.rename(old_path, new_path)
                        print(f"已还原: {filename} -> {new_name}")
                        restored_count += 1
                    except Exception as e:
                        print(f"还原 {filename} 时出错: {str(e)}")
            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")
                continue
    
    if dry_run:
        print(f"预览完成，共有 {restored_count} 个文件将被还原")
    else:
        print(f"还原完成，共还原了 {restored_count} 个文件")

def main():
    parser = argparse.ArgumentParser(description="将数字格式的文件名转换为中文章节名称或还原")
    parser.add_argument("folder", help="包含要处理文件的文件夹路径")
    parser.add_argument("--dry-run", action="store_true", help="预览将要执行的操作，但不实际执行")
    parser.add_argument("--restore", action="store_true", help="还原已重命名的文件到原始的数字格式")
    
    args = parser.parse_args()
    
    if args.restore:
        restore_files(args.folder, args.dry_run)
    else:
        rename_files(args.folder, args.dry_run)

if __name__ == "__main__":
    main()