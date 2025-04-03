#!/usr/bin/env python3

"""
章节分割音频生成脚本

此脚本会按照每5个章节进行分割，并生成对应的音频文件。
文件名会使用章节范围来命名，比如1-5.mp3表示第1章到第5章的内容。
"""

import asyncio
import os
import glob
import re
from concurrent.futures import ThreadPoolExecutor

import edge_tts

INPUT_DIR = "/Volumes/mydata/git/edge-tts/examples/output/siren/"
VOICE = "zh-CN-YunxiNeural"
CHAPTERS_PER_FILE = 5  # 每个音频文件包含的章节数
MAX_WORKERS = 8  # 并行处理的最大线程数

def split_into_chapters(text):
    """将文本按章节分割"""
    # 匹配章节标题的正则表达式，适配多种常见格式
    chapter_patterns = [
        r'第[一二三四五六七八九十百千万0-9]+章',  # 匹配 第X章
        r'Chapter\s*[0-9]+',  # 匹配 Chapter X
        r'\n\s*[0-9]+\s*\n'  # 匹配独立的数字作为章节号
    ]
    
    # 合并所有模式
    pattern = '|'.join(f'({p})' for p in chapter_patterns)
    
    # 查找所有章节开始位置
    chapters = []
    matches = list(re.finditer(pattern, text))
    
    # 如果没有找到任何章节标记，返回空列表
    if not matches:
        return []
    
    # 处理第一章
    first_match = matches[0]
    first_chapter_title = text[first_match.start():first_match.end()]
    
    # 处理所有章节
    for i in range(len(matches)):
        current_match = matches[i]
        current_title = text[current_match.start():current_match.end()]
        
        # 获取当前章节的内容（从当前标题到下一章标题或文本结束）
        content_start = current_match.end()
        content_end = matches[i + 1].start() if i < len(matches) - 1 else len(text)
        
        chapter_content = current_title + '\n' + text[content_start:content_end].strip()
        if chapter_content.strip():  # 确保章节内容不为空
            chapters.append(chapter_content)
    
    return chapters

def group_chapters(chapters):
    """将章节按照指定数量分组"""
    return [chapters[i:i + CHAPTERS_PER_FILE] 
            for i in range(0, len(chapters), CHAPTERS_PER_FILE)]

async def process_chapter_group(text: str, output_path: str, start_chapter: int, end_chapter: int, voice: str) -> None:
    """处理章节组并生成音频文件"""
    output_file = os.path.join(output_path, f"{start_chapter}-{end_chapter}.mp3")
    
    # 如果文本过长，按段落分割
    max_text_size = 5000  # 限制每次处理的文本大小为5KB
    if len(text.encode('utf-8')) > max_text_size:
        paragraphs = text.split('\n\n')
        current_text = ''
        temp_files = []
        
        for i, para in enumerate(paragraphs):
            if len(current_text.encode('utf-8')) + len(para.encode('utf-8')) > max_text_size:
                if current_text:
                    # 生成临时文件
                    temp_file = os.path.join(output_path, f"{start_chapter}-{end_chapter}_part{len(temp_files)}.mp3")
                    await process_text_chunk(current_text, temp_file, voice)
                    temp_files.append(temp_file)
                    current_text = para
            else:
                current_text = current_text + '\n\n' + para if current_text else para
        
        # 处理最后一块文本
        if current_text:
            temp_file = os.path.join(output_path, f"{start_chapter}-{end_chapter}_part{len(temp_files)}.mp3")
            await process_text_chunk(current_text, temp_file, voice)
            temp_files.append(temp_file)
        
        # 合并临时文件
        await merge_audio_files(temp_files, output_file)
        
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass
    else:
        # 直接处理文本
        await process_text_chunk(text, output_file, voice)

async def process_text_chunk(text: str, output_file: str, voice: str, max_retries: int = 3) -> None:
    """处理单个文本块并生成音频文件"""
    # 限制单个文本块的大小
    max_chunk_size = 2000  # 限制为2KB
    text_bytes = text.encode('utf-8')
    
    if len(text_bytes) > max_chunk_size:
        # 按句子分割文本
        sentences = re.split(r'([。！？])', text)
        current_chunk = ''
        temp_files = []
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else '')
            if len(current_chunk.encode('utf-8')) + len(sentence.encode('utf-8')) > max_chunk_size:
                if current_chunk:
                    # 生成临时文件
                    temp_file = f"{output_file}.part{len(temp_files)}"
                    await process_small_chunk(current_chunk, temp_file, voice, max_retries)
                    temp_files.append(temp_file)
                current_chunk = sentence
            else:
                current_chunk = current_chunk + sentence if current_chunk else sentence
        
        # 处理最后一块
        if current_chunk:
            temp_file = f"{output_file}.part{len(temp_files)}"
            await process_small_chunk(current_chunk, temp_file, voice, max_retries)
            temp_files.append(temp_file)
        
        # 合并临时文件
        await merge_audio_files(temp_files, output_file)
        
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass
    else:
        await process_small_chunk(text, output_file, voice, max_retries)

async def process_small_chunk(text: str, output_file: str, voice: str, max_retries: int) -> None:
    """处理较小的文本块并生成音频文件"""
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice, rate="+45%")
            with open(output_file, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"处理文本块时发生错误: {str(e)}，正在重试...")
            await asyncio.sleep(2 ** attempt + 1)  # 增加基础等待时间

async def merge_audio_files(input_files: list, output_file: str) -> None:
    """合并多个音频文件"""
    with open(output_file, 'wb') as outfile:
        for file_path in input_files:
            try:
                with open(file_path, 'rb') as infile:
                    outfile.write(infile.read())
            except Exception as e:
                print(f"合并音频文件时发生错误: {str(e)}")
                raise

async def process_file(input_file: str) -> None:
    """处理单个输入文件"""
    try:
        # 创建输出目录
        output_dir = os.path.splitext(os.path.basename(input_file))[0]
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"处理文件 {input_file}...")
        
        # 读取文件内容
        try:
            with open(input_file, "r", encoding="utf-8", errors="ignore") as file:
                text = file.read()
        except UnicodeError:
            with open(input_file, "r", encoding="latin1", errors="ignore") as file:
                text = file.read()
        
        if not text.strip():
            print(f"警告: {input_file} 文件内容为空")
            return
        
        # 分割章节并分组
        chapters = split_into_chapters(text)
        if not chapters:
            print(f"警告: 在文件 {input_file} 中未找到有效的章节")
            return
            
        print(f"找到 {len(chapters)} 个章节")
        chapter_groups = group_chapters(chapters)
        
        # 处理每组章节
        tasks = []
        for i, group in enumerate(chapter_groups):
            start_chapter = i * CHAPTERS_PER_FILE + 1
            end_chapter = start_chapter + len(group) - 1
            
            # 限制每个组的文本大小
            group_text = '\n'.join(group)
            if len(group_text.encode('utf-8')) > 10000:  # 限制为10KB
                print(f"警告: 章节 {start_chapter}-{end_chapter} 文本过长，尝试分割处理")
                # 按段落分割并重新组合
                paragraphs = group_text.split('\n\n')
                group_text = '\n\n'.join(p for p in paragraphs if p.strip())
            
            task = process_chapter_group(
                group_text, 
                output_dir, 
                start_chapter, 
                end_chapter, 
                VOICE
            )
            tasks.append(task)
            
            # 每处理5个任务就等待完成，避免并发请求过多
            if len(tasks) >= 5:
                await asyncio.gather(*tasks)
                tasks = []
        
        # 处理剩余的任务
        if tasks:
            await asyncio.gather(*tasks)
        
        print(f"完成处理 {output_dir}! 共生成 {len(chapter_groups)} 个音频文件。")
            
    except Exception as e:
        print(f"处理文件 {input_file} 时发生错误: {str(e)}")
        # 记录详细错误信息
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")

async def process_all_files() -> None:
    """并行处理所有输入文件"""
    input_files = glob.glob(os.path.join(INPUT_DIR, "*.txt"))
    
    if not input_files:
        print(f"在 {INPUT_DIR} 中未找到txt文件")
        return
    
    print(f"找到 {len(input_files)} 个文件需要处理")
    
    # 创建线程池并行处理文件
    tasks = [process_file(input_file) for input_file in input_files]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(process_all_files())
