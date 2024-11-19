import os

def split_file(input_file, output_dir, chunk_size):
    with open(input_file, 'rb') as f_in:
        for i, chunk in enumerate(iter(lambda: f_in.read(chunk_size), b'')):
            with open(os.path.join(output_dir, f"part_{i+1}"), 'wb') as f_out:
                f_out.write(chunk)

# 示例用法
input_file = "/Users/zhoujiangang/log/txt/1.txt"
output_dir = "/Users/zhoujiangang/log/txt/2.txt"
chunk_size = 524288  # 512KB
split_file(input_file, output_dir, chunk_size)