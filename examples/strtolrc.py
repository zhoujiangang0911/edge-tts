import re

def srt_to_lrc(srt_file, lrc_file):
    with open(srt_file, 'r', encoding='utf-8') as srt, open(lrc_file, 'w', encoding='utf-8') as lrc:
        timestamp = None
        content = ""
        for line in srt:
            # 匹配时间戳行
            time_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> ', line)
            if time_match:
                # 如果有之前的内容，先写入
                if timestamp and content:
                    lrc.write(f"{timestamp}{content}\n")
                # 提取时间并转换为LRC格式
                hh, mm, ss, ms = time_match.groups()
                total_minutes = int(hh) * 60 + int(mm)
                timestamp = f"[{total_minutes:02}:{int(ss):02}.{int(ms[:2]):02}]"
                content = ""
            # 匹配字幕编号
            elif re.match(r'^\d+$', line.strip()):
                continue
            # 收集字幕内容
            elif line.strip():
                content = line.strip()
        # 写入最后一条字幕
        if timestamp and content:
            lrc.write(f"{timestamp}{content}\n")

# 使用方法
srt_to_lrc("/Volumes/mydata/git/edge-tts/examples/output/test/hello.srt", "/Volumes/mydata/git/edge-tts/examples/output/test/hello.lrc")
print("转换完成！")