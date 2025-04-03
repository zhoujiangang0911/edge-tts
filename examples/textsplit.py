import os
import re

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

def split_book_into_files(input_file, output_dir, chapters_per_file=2):
    """将电子书按章节分割成多个文件"""
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
        
        if not text.strip():
            print(f"警告: {input_file} 文件内容为空")
            return
        
        # 分割章节
        chapters = split_into_chapters(text)
        if not chapters:
            print(f"警告: 在文件 {input_file} 中未找到有效的章节")
            return
            
        print(f"找到 {len(chapters)} 个章节")
        
        # 按指定数量分组并保存
        for i in range(0, len(chapters), chapters_per_file):
            group = chapters[i:i + chapters_per_file]
            start_chapter = i + 1
            end_chapter = min(i + len(group), len(chapters))
            
            # 创建输出文件名
            output_file = os.path.join(output_dir, f"{start_chapter}-{end_chapter}.txt")
            
            # 写入文件
            with open(output_file, "w", encoding=used_encoding) as f:
                f.write('\n\n'.join(group))
            
            print(f"已保存章节 {start_chapter}-{end_chapter} 到文件: {output_file}")
        
        print(f"完成! 共生成 {(len(chapters) + chapters_per_file - 1) // chapters_per_file} 个文件。")
            
    except Exception as e:
        print(f"处理文件时发生错误: {str(e)}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")

# 使用示例
if __name__ == "__main__":
    input_file = "/Volumes/mydata/git/edge-tts/examples/output/十日终焉.txt"  # 输入文件路径
    output_dir = "/Volumes/mydata/git/edge-tts/examples/output/srzy/"     # 输出目录
    split_book_into_files(input_file, output_dir)