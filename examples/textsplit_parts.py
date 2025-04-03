import os
import re

def split_into_parts_and_chapters(text):
    """将文本按部和章节分割"""
    # 匹配部和章节标题的正则表达式
    part_pattern = r'第[一二三四五六七八九十百千万0-9]+部[^\n]*'
    chapter_pattern = r'[^\n]*第[一二三四五六七八九十百千万0-9]+章[^\n]*'
    
    # 先按部分割文本
    parts = []
    part_matches = list(re.finditer(part_pattern, text))
    
    if not part_matches:
        # 如果没有找到部，则将整个文本作为一个部处理
        chapters = split_chapters(text)
        if chapters:
            parts.append(('未命名部', chapters))
    else:
        # 处理每一部分
        for i in range(len(part_matches)):
            current_match = part_matches[i]
            part_title = text[current_match.start():current_match.end()].strip()
            
            # 获取当前部的内容
            content_start = current_match.end()
            content_end = part_matches[i + 1].start() if i < len(part_matches) - 1 else len(text)
            part_content = text[content_start:content_end].strip()
            
            # 分割章节
            chapters = split_chapters(part_content)
            if chapters:
                parts.append((part_title, chapters))
    
    return parts

def split_chapters(text):
    """将文本按章节分割"""
    chapter_pattern = r'[^\n]*第[一二三四五六七八九十百千万0-9]+章[^\n]*'
    chapters = []
    
    matches = list(re.finditer(chapter_pattern, text))
    if not matches:
        return []
    
    for i in range(len(matches)):
        current_match = matches[i]
        chapter_title = text[current_match.start():current_match.end()].strip()
        
        # 获取章节内容
        content_start = current_match.end()
        content_end = matches[i + 1].start() if i < len(matches) - 1 else len(text)
        chapter_content = chapter_title + '\n' + text[content_start:content_end].strip()
        
        if chapter_content.strip():
            chapters.append(chapter_content)
    
    return chapters

def split_book_into_files(input_file, output_dir, chapters_per_file=2):
    """将电子书按章节分割成多个文件，保持部的结构"""
    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 尝试不同的编码读取文件
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
        text = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(input_file, 'r', encoding=encoding) as file:
                    text = file.read()
                used_encoding = encoding
                break
            except UnicodeError:
                continue
        
        if text is None:
            print(f"错误: 无法使用任何已知编码读取文件 {input_file}")
            return
        
        print(f"成功使用 {used_encoding} 编码读取文件")
        
        # 分割部和章节
        parts = split_into_parts_and_chapters(text)
        if not parts:
            print(f"警告: 在文件 {input_file} 中未找到有效的章节")
            return
        
        total_chapters = sum(len(chapters) for _, chapters in parts)
        print(f"找到 {len(parts)} 个部分，共 {total_chapters} 个章节")
        
        # 为每个部创建子目录
        for part_index, (part_title, chapters) in enumerate(parts, 1):
            part_dir = os.path.join(output_dir, f"{part_index:02d}-{part_title}")
            os.makedirs(part_dir, exist_ok=True)
            
            # 按指定数量分组并保存章节
            for i in range(0, len(chapters), chapters_per_file):
                group = chapters[i:i + chapters_per_file]
                start_chapter = i + 1
                end_chapter = min(i + len(group), len(chapters))
                
                # 创建输出文件名
                output_file = os.path.join(part_dir, f"{start_chapter:02d}-{end_chapter:02d}.txt")
                
                # 写入文件
                with open(output_file, "w", encoding=used_encoding) as f:
                    f.write('\n\n'.join(group))
                
                print(f"已保存 {part_title} 的章节 {start_chapter}-{end_chapter} 到文件: {output_file}")
        
        print(f"完成! 文件已按部分组织并保存在目录: {output_dir}")
            
    except Exception as e:
        print(f"处理文件时发生错误: {str(e)}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")

# 使用示例
if __name__ == "__main__":
    input_file = "/Volumes/mydata/git/edge-tts/examples/output/诡秘之主.txt"  # 输入文件路径
    output_dir = "/Volumes/mydata/git/edge-tts/examples/output/test/"     # 输出目录
    split_book_into_files(input_file, output_dir, chapters_per_file=2)  # 每2章一个文件