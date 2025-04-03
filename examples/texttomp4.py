#!/usr/bin/env python3

"""批量文本转语音程序

这个程序用于将指定目录下的所有txt文件转换为语音文件。
使用多线程处理以提高效率，并支持大文件分块处理。
"""

import asyncio
import os
import glob
import re
from typing import List

import edge_tts

# 配置参数
VOICE = "zh-CN-YunxiNeural"  # 默认使用云溪声音
MAX_RETRIES = 3  # 最大重试次数

async def process_chunk(text: str, output_file: str, voice: str) -> None:
    """处理单个文本块并生成音频文件"""
    for attempt in range(MAX_RETRIES):
        try:
            communicate = edge_tts.Communicate(text, voice, rate="+45%")
            with open(output_file, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        if not isinstance(chunk["data"], bytes):
                            raise ValueError(f"接收到的音频数据格式错误: {type(chunk['data'])}")
                        file.write(chunk["data"])
            return
        except UnicodeError as e:
            print(f"处理文件 {output_file} 时发生编码错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: 字符位置 {e.start} 到 {e.end}")
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"正在进行第 {attempt + 1} 次重试...")
            await asyncio.sleep(2 ** attempt + 1)
        except Exception as e:
            print(f"处理文件 {output_file} 时发生错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"正在进行第 {attempt + 1} 次重试...")
            await asyncio.sleep(2 ** attempt + 1)

async def process_file(input_file: str, output_dir: str) -> None:
    """处理单个文件"""
    try:
        # 检查文件扩展名
        if not input_file.lower().endswith('.txt'):
            print(f"跳过非txt文件: {input_file}")
            return
            
        # 创建输出目录
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{file_name}.mp3")
        
        print(f"正在处理文件: {input_file}")
        
        # 读取文件内容
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'latin1']
        text = None
        successful_encoding = None
        file_size = os.path.getsize(input_file)
        
        # 检查文件大小
        if file_size == 0:
            print(f"警告: {input_file} 文件为空")
            return
            
        # 先尝试以二进制模式读取文件头部来检测编码
        with open(input_file, 'rb') as file:
            raw_data = file.read(min(file_size, 4096))  # 读取前4KB用于编码检测
            
        # 尝试不同的编码
        for encoding in encodings:
            try:
                # 先尝试解码文件头部来验证编码
                raw_data.decode(encoding)
                # 如果解码成功，则读取整个文件
                with open(input_file, "r", encoding=encoding) as file:
                    text = file.read()
                successful_encoding = encoding
                break
            except UnicodeError:
                continue
        
        if text is None:
            raise UnicodeError(f"无法使用以下编码读取文件：{', '.join(encodings)}")
        
        print(f"使用 {successful_encoding} 编码成功读取文件")
        
        if not text.strip():
            print(f"警告: {input_file} 文件内容为空")
            return
            
        # 直接处理整个文本文件
        print(f"正在生成音频: {file_name}...")
        await process_chunk(text, output_file, VOICE)
        print(f"已生成 {os.path.basename(output_file)}")
        
        print(f"文件 {file_name} 处理完成！")
            
    except Exception as e:
        print(f"处理文件 {input_file} 时发生错误: {str(e)}")

def extract_number(filename: str) -> int:
    """从文件名中提取数字，如果没有数字则返回最大值"""
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else float('inf')

async def process_directory(input_dir: str, output_dir: str) -> None:
    """处理指定目录下的所有txt文件"""
    # 获取所有txt文件
    input_files = glob.glob(os.path.join(input_dir, "*.txt"))
    
    if not input_files:
        print(f"在目录 {input_dir} 中未找到txt文件")
        return
    
    # 过滤掉已经处理过的文件（文件名包含_success）
    input_files = [f for f in input_files if "_success" not in os.path.basename(f)]
    
    if not input_files:
        print("所有文件都已处理完成")
        return
    
    # 按文件名中的数字排序
    input_files.sort(key=lambda x: extract_number(os.path.basename(x)))
    
    print(f"找到 {len(input_files)} 个待处理的txt文件")
    print("文件将按照数字顺序处理")
    
    # 顺序处理每个文件
    for input_file in input_files:
        await process_file(input_file, output_dir)
        # 处理成功后重命名原文件
        file_dir = os.path.dirname(input_file)
        file_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(file_name)[0]
        new_name = os.path.join(file_dir, f"{name_without_ext}_success.txt")
        os.rename(input_file, new_name)
        print(f"已将原文件重命名为: {os.path.basename(new_name)}")


def main():
    """主函数"""
    import argparse
    
    # 声明全局变量
    global VOICE, CHUNK_SIZE, MAX_WORKERS
    
    parser = argparse.ArgumentParser(description="批量将txt文件转换为语音文件")
    parser.add_argument("input_dir", help="输入目录路径，包含要转换的txt文件")
    parser.add_argument("output_dir", help="输出目录路径，用于保存生成的音频文件")
    parser.add_argument("--voice", default=VOICE, help=f"语音角色，默认为{VOICE}")
    
    args = parser.parse_args()
    
    # 更新全局配置
    VOICE = args.voice
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 运行转换程序
    asyncio.run(process_directory(args.input_dir, args.output_dir))

if __name__ == "__main__":
    main()