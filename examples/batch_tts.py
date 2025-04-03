import os
import subprocess
import argparse
from pathlib import Path

def process_txt_files(input_dir=None, output_dir=None, voice="zh-CN-YunxiNeural", rate="+45%"):
    # 获取输入目录
    current_dir = Path(input_dir) if input_dir else Path.cwd()
    
    # 创建mp3输出目录
    mp3_dir = Path(output_dir) if output_dir else current_dir / "mp3"
    mp3_dir.mkdir(exist_ok=True)
    
    # 获取所有txt文件
    txt_files = list(current_dir.glob("*.txt"))
    total_files = len(txt_files)
    
    if total_files == 0:
        print("指定目录下没有找到txt文件")
        return
    
    print(f"找到 {total_files} 个txt文件，开始处理...")
    
    # 处理每个txt文件
    for index, txt_file in enumerate(txt_files, 1):
        try:
            # 生成对应的mp3文件名
            mp3_file = mp3_dir / f"{txt_file.stem}.mp3"
            
            print(f"[{index}/{total_files}] 正在处理: {txt_file.name}")
            
            # 构建edge-tts命令
            cmd = [
                "edge-tts",
                "-f", str(txt_file),
                "--write-media", str(mp3_file),
                "-v", voice,
                "--rate", rate
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ 成功生成: {mp3_file.name}")
            else:
                print(f"✗ 处理失败: {txt_file.name}")
                print(f"错误信息: {result.stderr}")
                
        except Exception as e:
            print(f"✗ 处理文件 {txt_file.name} 时发生错误: {str(e)}")
    
    print("\n处理完成!")
    print(f"输出目录: {mp3_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量将txt文件转换为mp3")
    parser.add_argument("-i", "--input", help="输入目录路径，默认为当前目录")
    parser.add_argument("-o", "--output", help="输出目录路径，默认为输入目录下的mp3文件夹")
    parser.add_argument("-v", "--voice", default="zh-CN-YunxiNeural", help="语音角色，默认为zh-CN-YunxiNeural")
    parser.add_argument("-r", "--rate", default="+45%", help="语速，默认为+45%")
    
    args = parser.parse_args()
    process_txt_files(args.input, args.output, args.voice, args.rate)