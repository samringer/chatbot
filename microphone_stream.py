# Utilities to start microphone on a macbook.
# Based on https://docs.speechmatics.com/introduction/rt-guide

from contextlib import contextmanager
import os
import time
import pyaudio
import asyncio

START_TIME = time.time()


class AudioProcessor:
    def __init__(self, sample_rate: int, sample_width: int, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.chunk_size = chunk_size
        self.wave_data = bytearray()
        self.read_offset = 0

    async def read_chunk(self):
        while self.read_offset + self.chunk_size > len(self.wave_data):
            await asyncio.sleep(0.001)
        new_offset = self.read_offset + self.chunk_size
        data = self.wave_data[self.read_offset:new_offset]
        self.read_offset = new_offset
        return data

    def write_audio(self, data):
        self.wave_data.extend(data)
        return


@contextmanager
def get_microphone_stream(is_safe_to_record: asyncio.Event | None = None):
    
    if is_safe_to_record is None:
        # Assume it is always safe to record.
        is_safe_to_record = asyncio.Event()
        is_safe_to_record.set()

    # Assembly want pretty large chunks
    chunk_size = os.environ.get('CHUNK_SIZE', 16_000)

    # Get microphone stats
    p = pyaudio.PyAudio()
    device_index = p.get_default_input_device_info()['index']
    #sample_width = p.get_sample_size(pyaudio.paInt32)
    sample_width = p.get_sample_size(pyaudio.paInt16)
    sample_rate = int(p.get_device_info_by_index(device_index)['defaultSampleRate'])

    audio_processor = AudioProcessor(sample_rate=sample_rate, sample_width=sample_width, chunk_size=chunk_size)

    def stream_callback(in_data, frame_count, time_info, status):
        if is_safe_to_record.is_set():
            audio_processor.write_audio(in_data)
        return in_data, pyaudio.paContinue

    #stream = p.open(format=pyaudio.paInt32,
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk_size,
                    input_device_index=device_index,
                    stream_callback=stream_callback,
    )
    print("Mic stream opened")
    yield audio_processor
    p.terminate()
    stream.stop_stream()
    stream.close()
        

async def main():
    safe_to_record = asyncio.Event()
    safe_to_record.set()
    with get_microphone_stream(safe_to_record) as microphone_stream:
        await asyncio.sleep(5)
            

if __name__ == "__main__":
    asyncio.run(main())
    