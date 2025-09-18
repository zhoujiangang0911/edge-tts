import os
import subprocess
import sys
import argparse

def run_cmd(cmd):
    """运行命令行并检查错误"""
    print(">>>", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"命令执行失败：{' '.join(cmd)}")

def convert_mp3_to_m4a(files):
    """把 MP3 转成 m4a (AAC)"""
    converted_files = []
    for f in files:
        output = f"{os.path.splitext(f)[0]}.m4a"
        run_cmd(["ffmpeg", "-y", "-i", f, "-c:a", "aac", "-b:a", "128k", output])
        converted_files.append(output)
    return converted_files

def merge_m4a(files, output="all.m4b"):
    """合并 m4a 文件为 m4b"""
    with open("file_list.txt", "w") as f:
        for fpath in files:
            f.write(f"file '{os.path.abspath(fpath)}'\n")
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", "file_list.txt", "-c", "copy", output])
    return output

def generate_chapters(files, output="chapters.txt"):
    """生成章节文件"""
    start = 0
    with open(output, "w", encoding="utf-8") as out:
        out.write(";FFMETADATA1\n")
        for f in files:
            # 获取时长
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", f],
                capture_output=True, text=True
            )
            duration = float(result.stdout.strip())
            end = start + int(duration * 1000)
            title = os.path.splitext(os.path.basename(f))[0]
            out.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={start}\nEND={end}\ntitle={title}\n\n")
            start = end
    return output

def mux_metadata(input_m4b, metadata_file, output_m4b, title=None, author=None, cover=None):
    """合并章节和元数据"""
    cmd = ["ffmpeg", "-y", "-i", input_m4b, "-i", metadata_file]
    if cover:
        cmd.extend(["-i", cover])

    # Map metadata from the chapters file (input 1)
    cmd.extend(["-map_metadata", "1"])

    # Handle streams and codecs
    if cover:
        # If there is a cover, map audio and video, and set codecs individually.
        # Audio is copied, video (cover) is re-encoded to png.
        cmd.extend(["-map", "0", "-map", "2", "-c:a", "copy", "-c:v", "png", "-disposition:v", "attached_pic"])
    else:
        # If no cover, just copy the audio stream.
        cmd.extend(["-c", "copy"])

    if title:
        cmd.extend(["-metadata", f"title={title}"])
    if author:
        cmd.extend(["-metadata", f"artist={author}", "-metadata", f"author={author}"])
    cmd.append(output_m4b)
    run_cmd(cmd)

def main():
    parser = argparse.ArgumentParser(description="将多个MP3合并为带章节的M4B有声书")
    parser.add_argument("--title", help="书名")
    parser.add_argument("--author", help="作者")
    parser.add_argument("--cover", help="封面图片（可选）")
    parser.add_argument("--output", default="final.m4b", help="输出文件名")
    args = parser.parse_args()

    # 1. 找到所有 MP3 文件
    files = sorted([f for f in os.listdir('.') if f.lower().endswith(".mp3")])
    if not files:
        sys.exit("当前文件夹没有找到 MP3 文件")

    # 2. 转码
    m4a_files = convert_mp3_to_m4a(files)

    # 3. 合并
    merged = merge_m4a(m4a_files)

    # 4. 生成章节文件
    chapters = generate_chapters(m4a_files)

    # 5. 添加章节和元数据
    mux_metadata(merged, chapters, args.output, title=args.title, author=args.author, cover=args.cover)

    print(f"\n✅ 完成！输出文件：{args.output}")

if __name__ == "__main__":
    main()
