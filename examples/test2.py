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
from concurrent.futures import ThreadPoolExecutor, as_completed

import edge_tts

INPUT_DIR = "/Users/zhoujiangang/log/txt/smfs"
VOICE = "zh-CN-YunxiNeural"
CHUNK_SIZE = 5000  # Characters per chunk
MAX_WORKERS = 8  # Number of parallel processes


async def process_chunk(text: str, output_path: str, file_number: int, voice: str) -> None:
    """Process a single chunk of text and save to MP3"""
    output_file = os.path.join(output_path, f"{os.path.basename(output_path)}_{file_number}.mp3")
    communicate = edge_tts.Communicate(text, voice, rate="+45%")
    with open(output_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])


async def process_file(input_file: str) -> None:
    """Process a single input file"""
    try:
        # Create output directory with same name as input file (without extension)
        output_dir = os.path.basename(input_file)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Processing {input_file}...")
        
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
            print(f"Warning: {input_file} appears to be empty after decoding")
            return
            
        # Process text in chunks
        chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        
        # Process each chunk and create MP3 files
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():  # Skip empty chunks
                continue
            print(f"Processing {output_dir} chunk {i} of {len(chunks)}...")
            await process_chunk(chunk, output_dir, i, VOICE)
            print(f"Generated {output_dir}_{i}.mp3")
        
        print(f"Completed processing {output_dir}! Generated {len(chunks)} MP3 files.")
            
    except Exception as e:
        print(f"Error processing file {input_file}: {e}")


async def process_all_files() -> None:
    """Process all input files in parallel"""
    # Get all input files
    input_files = glob.glob(os.path.join(INPUT_DIR, "smfs_*"))
    
    if not input_files:
        print(f"No input files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(input_files)} files to process")
    
    # Create thread pool for parallel processing
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create tasks for each file
        tasks = [
            loop.create_task(process_file(input_file))
            for input_file in input_files
        ]
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(process_all_files())
