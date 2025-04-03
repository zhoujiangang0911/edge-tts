#!/usr/bin/env python3

import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import argparse
import re

def clean_text(text):
    """Clean and format text content"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove empty brackets
    text = re.sub(r'\[\s*\]', '', text)
    # Remove special characters but keep Chinese characters and punctuation
    text = re.sub(r'[^\u4e00-\u9fff\w\s.,!?，。！？、：；]', '', text)
    return text.strip()

def is_valid_line(text):
    """Check if a line of text is valid (not too long)"""
    return len(text) <= 500

def extract_chapter_number(text):
    """Extract chapter number from text"""
    patterns = [
        r'第([0-9零一二三四五六七八九十百千]+)[章节篇回]',
        r'Chapter\s*([0-9]+)',
        r'^\s*([0-9]+)\s*[章节篇回]'
    ]
    
    chinese_nums = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
                   '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
                   '十': 10}
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = match.group(1)
            if any(c in num for c in chinese_nums):
                try:
                    if len(num) == 1:
                        return chinese_nums[num]
                    elif len(num) == 2 and num[0] == '十':
                        return 10 + chinese_nums.get(num[1], 0)
                    elif len(num) == 2:
                        return chinese_nums[num[0]] * 10 + chinese_nums.get(num[1], 0)
                except:
                    return 9999
            try:
                return int(num)
            except:
                return 9999
    return 9999

def extract_chapter_info(soup):
    """Extract chapter title and content"""
    title = ""
    content = []
    chapter_num = 9999
    
    # Find chapter title
    title_tag = None
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        text = clean_text(tag.get_text())
        if text and ('章' in text or '节' in text or 'Chapter' in text):
            title = text
            chapter_num = extract_chapter_number(text)
            title_tag = tag
            break
    
    # If no title in headers, check first paragraph
    if not title:
        first_p = soup.find(['p', 'div'])
        if first_p:
            text = clean_text(first_p.get_text())
            if text and ('章' in text or '节' in text or 'Chapter' in text):
                title = text
                chapter_num = extract_chapter_number(text)
                title_tag = first_p
    
    # Remove the title tag after extracting it
    if title_tag:
        title_tag.decompose()
    
    # Get content paragraphs, excluding the title
    for paragraph in soup.find_all(['p', 'div']):
        text = clean_text(paragraph.get_text())
        if text and len(text) > 10:  # Only add substantial paragraphs
            if text != title and is_valid_line(text):  # Check line length
                content.append(text)
    
    return chapter_num, title, content

def epub_to_text(epub_path, output_dir):
    """Convert EPUB file to TXT format"""
    try:
        book = epub.read_epub(epub_path)
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(epub_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.txt")
        
        # Store chapters for sorting
        chapters = []
        seen_titles = set()
        
        # Process each chapter
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    html_content = item.get_content().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'head', 'meta', 'header']):
                        element.decompose()
                    
                    # Extract chapter info
                    chapter_num, title, content = extract_chapter_info(soup)
                    
                    if content and title and title not in seen_titles:
                        chapters.append((chapter_num, title, content))
                        seen_titles.add(title)
                    elif content and not title:
                        # Handle content without explicit chapter title
                        chapters.append((chapter_num, None, content))
                
                except Exception as e:
                    print(f"Warning: Error processing chapter in {epub_path}: {e}")
                    continue
        
        # Sort chapters by number
        chapters.sort(key=lambda x: x[0])
        
        # Write chapters to file
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, (_, title, content) in enumerate(chapters, 1):
                # Write chapter title
                if title:
                    f.write(f"{title}\n")
                else:
                    f.write(f"第{i}章\n")
                
                # Write chapter content without empty lines
                for paragraph in content:
                    if paragraph.strip():  # Only write non-empty paragraphs
                        f.write(f"{paragraph}\n")
        
        if chapters:
            print(f"Successfully converted {epub_path} to {output_file} ({len(chapters)} chapters)")
            return output_file
        else:
            print(f"Warning: No valid content found in {epub_path}")
            return None
        
    except Exception as e:
        print(f"Error converting {epub_path}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Convert EPUB files to TXT format')
    parser.add_argument('input_path', help='Path to EPUB file or directory containing EPUB files')
    parser.add_argument('--output-dir', default='output', help='Output directory for TXT files')

    args = parser.parse_args()
    
    if os.path.isfile(args.input_path):
        epub_to_text(args.input_path, args.output_dir)
    elif os.path.isdir(args.input_path):
        success_count = 0
        total_count = 0
        for filename in os.listdir(args.input_path):
            if filename.lower().endswith('.epub'):
                total_count += 1
                epub_path = os.path.join(args.input_path, filename)
                if epub_to_text(epub_path, args.output_dir):
                    success_count += 1
        
        print(f"\nConversion complete: {success_count}/{total_count} files converted successfully")
    else:
        print(f"Error: {args.input_path} is not a valid file or directory")

if __name__ == "__main__":
    main()
