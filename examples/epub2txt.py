#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def clean_text(content):
    """清理HTML标签，保留纯文本内容"""
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(content, 'html.parser')
    # 获取文本内容
    text = soup.get_text()
    # 清理多余的空白字符
    text = re.sub(r'\s+', '\n', text.strip())
    return text

def epub_to_txt(epub_path, txt_path):
    """将epub文件转换为txt文件"""
    try:
        # 读取epub文件
        book = epub.read_epub(epub_path)
        
        # 打开txt文件用于写入
        with open(txt_path, 'w', encoding='utf-8') as f:
            # 获取所有文档
            for item in book.get_items():
                # 只处理文本内容
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # 获取内容并解码
                    content = item.get_content().decode('utf-8')
                    # 清理文本
                    text = clean_text(content)
                    # 写入文件，确保章节间有足够的分隔
                    if text.strip():
                        f.write(text + '\n\n')
        
        print(f'转换完成！输出文件：{txt_path}')
        return True
    except Exception as e:
        print(f'转换失败：{str(e)}')
        return False

def main():
    if len(sys.argv) != 2:
        print('使用方法：python epub2txt.py <epub文件路径>')
        sys.exit(1)
    
    epub_path = sys.argv[1]
    if not os.path.exists(epub_path):
        print(f'错误：文件 {epub_path} 不存在')
        sys.exit(1)
    
    # 生成输出文件路径
    txt_path = os.path.splitext(epub_path)[0] + '.txt'
    
    # 转换文件
    epub_to_txt(epub_path, txt_path)

if __name__ == '__main__':
    main()