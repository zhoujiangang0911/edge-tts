import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, USLT

def srt_to_uslt(srt_file, mp3_file):
    # 读取SRT文件内容
    with open(srt_file, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    # 解析SRT内容
    lyrics = []
    timestamps = []
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> .*?\n(.*?)\n\n', re.DOTALL)
    matches = pattern.finditer(srt_content)

    for match in matches:
        timestamp = match.group(2)
        # 转换时间戳格式从 HH:MM:SS,mmm 到毫秒时间
        # 先分割毫秒部分
        time_parts = timestamp.split(',')
        time_without_ms = time_parts[0]
        ms = int(time_parts[1])
        # 再处理时分秒部分
        h, m, s = map(int, time_without_ms.split(':'))
        # 计算总毫秒数
        total_ms = (h * 3600 + m * 60 + s) * 1000 + ms
        
        text = match.group(3).strip()
        # 只保存纯文本内容，不包含时间戳
        lyrics.append(text)
        # 单独保存时间戳（毫秒）
        timestamps.append(total_ms)

    # 将所有字幕内容合并成一个字符串，每行一个歌词
    full_lyrics = '\n'.join(lyrics)

    # 将歌词写入MP3文件
    try:
        # 尝试加载现有的ID3标签
        audio = MP3(mp3_file, ID3=ID3)
    except:
        # 如果没有ID3标签，创建一个新的
        audio = MP3(mp3_file)
        audio.add_tags()

    # 创建USLT标签
    # 创建同步歌词格式，将时间戳和歌词文本组合
    synced_lyrics = []
    for i in range(len(lyrics)):
        # 将毫秒转换为秒
        time_in_seconds = timestamps[i] / 1000.0
        synced_lyrics.append((time_in_seconds, lyrics[i]))
    
    uslt_tag = USLT(
        encoding=3,  # UTF-8
        lang='eng',  # 语言代码
        desc='',     # 描述
        text=full_lyrics,
        sync=False   # 不在文本中显示时间戳
    )
    
    # 设置同步歌词
    uslt_tag.text = full_lyrics
    uslt_tag.sync_text = synced_lyrics

    # 添加USLT标签到MP3文件
    audio.tags.add(uslt_tag)
    audio.save()

# 使用示例
srt_to_uslt('/Volumes/mydata/git/edge-tts/examples/output/test/hello.srt', '/Volumes/mydata/git/edge-tts/examples/output/test/hello.mp3')