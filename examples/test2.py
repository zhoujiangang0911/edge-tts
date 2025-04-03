#!/usr/bin/env python3

"""
Basic audio streaming example.

This example shows how to stream the audio data from the TTS engine,
and how to get the WordBoundary events from the engine (which could
be ignored if not needed).

The example streaming_with_subtitles.py shows how to use the
WordBoundary events to create subtitles using SubMaker.
"""

import asyncio
import os
import glob
import re
from concurrent.futures import ThreadPoolExecutor

import edge_tts

INPUT_DIR = "/Volumes/mydata/git/edge-tts/examples/output/guimi"
VOICE = "zh-CN-YunxiNeural"
MAX_WORKERS = 4  # Number of parallel processes
CHAPTERS_PER_FILE = 2  # Number of chapters to combine into one audio file


def extract_chapter_title(text):
    """Extract chapter title from text"""
    patterns = [
        r'(第[0-9零一二三四五六七八九十百千]+[章节篇回].*?)[\n\r]',
        r'(Chapter\s*[0-9]+.*?)[\n\r]',
        r'(^[0-9]+\s*[章节篇回].*?)[\n\r]'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    
    return None


def split_text_into_chapters(text):
    """Split text into chapters based on chapter titles"""
    # Patterns to identify chapter beginnings
    patterns = [
        r'第[0-9零一二三四五六七八九十百千]+[章节篇回]',
        r'Chapter\s*[0-9]+',
        r'^[0-9]+\s*[章节篇回]'
    ]
    
    # Combine patterns into a single regex
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    
    # Find all potential chapter starts
    chapter_starts = []
    for match in re.finditer(combined_pattern, text, re.MULTILINE):
        chapter_starts.append(match.start())
    
    # If no chapters found, return the entire text as one chapter
    if not chapter_starts:
        return [("Chapter 1", text)]
    
    # Split text into chapters
    chapters = []
    for i, start in enumerate(chapter_starts):
        # Extract chapter title
        end_of_title = text.find('\n', start)
        if end_of_title == -1:
            end_of_title = len(text)
        title = text[start:end_of_title].strip()
        
        # Extract chapter content
        if i < len(chapter_starts) - 1:
            content = text[start:chapter_starts[i+1]]
        else:
            content = text[start:]
        
        chapters.append((title, content))
    
    return chapters


async def process_chapter_group(txt_path, output_path, group_number, title, voice):
    """从保存的txt文件生成音频"""
    # 读取保存的分割文件
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            combined_text = f.read()
    except Exception as e:
        print(f"无法读取分割文件 {txt_path}: {e}")
        return None

    # 生成文件名
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
    if len(safe_title) > 50:
        safe_title = safe_title[:47] + "..."
        
    output_file = os.path.join(output_path, f"{group_number}_{safe_title}.mp3")
    
    # 生成音频
    communicate = edge_tts.Communicate(combined_text, voice, rate="+45%")
    with open(output_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
    
    # 清理临时文本文件
    try:
        os.remove(txt_path)
        print(f"已清理临时文件: {txt_path}")
    except Exception as e:
        print(f"清理临时文件失败: {e}")
    
    return output_file


def group_chapters(chapters, chapters_per_file):
    """Group chapters into batches for processing"""
    grouped_chapters = []
    for i in range(0, len(chapters), chapters_per_file):
        group = chapters[i:i + chapters_per_file]
        first_title = group[0][0]
        last_title = group[-1][0]
        combined_title = first_title if first_title == last_title else f"{first_title}至{last_title}"
        combined_content = "\n\n".join([f"{title}\n{content}" for title, content in group])
        
        # 添加章节组编号到分组信息
        grouped_chapters.append({
            "title": combined_title,
            "content": combined_content,
            "group_num": i // chapters_per_file + 1,
            "file_name": f"group_{i//chapters_per_file + 1}.txt"  # 添加文件名字段
        })
    
    return grouped_chapters


async def process_file(input_file):
    """Process a single input file"""
    try:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = base_name
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"处理文件: {input_file}...")
        
        # Try different encoding strategies
        try:
            # First try UTF-8 with error handling
            with open(input_file, "r", encoding="utf-8", errors="ignore") as file:
                text = file.read()
        except UnicodeError:
            # If that fails, try with a different encoding
            with open(input_file, "r", encoding="latin1", errors="ignore") as file:
                text = file.read()
        
        if not text.strip():
            print(f"警告: {input_file} 解码后似乎是空的")
            return
        
        # 第一步: 分割章节
        print(f"分割章节...")
        chapters = split_text_into_chapters(text)
        print(f"找到 {len(chapters)} 个章节")
        
        # 第二步: 将章节分组，每组CHAPTERS_PER_FILE个章节
        print(f"将章节分组，每组 {CHAPTERS_PER_FILE} 个章节...")
        grouped_chapters = group_chapters(chapters, CHAPTERS_PER_FILE)
        print(f"创建了 {len(grouped_chapters)} 个章节组")

        # 新增步骤: 保存章节组到txt文件
        print("保存章节组文本文件...")
        for group in grouped_chapters:
            txt_path = os.path.join(output_dir, group["file_name"])
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(group["content"])
            print(f"已保存: {txt_path}")

        # 第三步: 为每组章节创建任务（修改为读取txt文件）
        tasks = []
        for group in grouped_chapters:
            txt_path = os.path.join(output_dir, group["file_name"])
            print(f"创建任务处理章节组 {group['group_num']}: {group['title']}")
            
            task = asyncio.create_task(
                process_chapter_group(txt_path, output_dir, group["group_num"], group["title"], VOICE)
            )
            tasks.append(task)
        
        # 第四步: 并行执行所有任务
        print(f"开始并行处理所有章节组...")
        results = await asyncio.gather(*tasks)
        
        print(f"完成处理 {base_name}! 生成了 {len(results)} 个MP3文件。")
        for result in results:
            print(f"- 生成文件: {os.path.basename(result)}")
            
    except Exception as e:
        print(f"处理文件 {input_file} 时出错: {e}")


async def process_all_files():
    """Process all input files in parallel"""
    # Get all input files
    input_files = glob.glob(os.path.join(INPUT_DIR, "*.txt"))
    
    if not input_files:
        print(f"在 {INPUT_DIR} 中没有找到输入文件")
        return
    
    print(f"找到 {len(input_files)} 个文件需要处理")
    
    # Process each file sequentially, but process chapters within each file in parallel
    for input_file in input_files:
        await process_file(input_file)
    
    print("所有文件处理完成!")


if __name__ == "__main__":
    asyncio.run(process_all_files())
