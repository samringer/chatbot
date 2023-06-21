from contextlib import asynccontextmanager
import os
import websockets
import asyncio
import base64
import json

from microphone_stream import get_microphone_stream


async def stream_audio_to_assembly(microphone_stream, ws_client):
    while True:
        audio_chunk = await microphone_stream.read_chunk()
        audio_chunk = base64.b64encode(audio_chunk).decode("utf-8")
        payload = json.dumps({"audio_data":str(audio_chunk)})

        await ws_client.send(payload)
        

async def get_transcripts_from_websocket(ws_client):
    while True:
        message = await ws_client.recv()
        message = json.loads(message)
        if message['message_type'] == "FinalTranscript":
            yield message['text']
            

async def session_heartbeat(ws_client):
    # Assembly kills sessions after 1 minute of inactivity.
    # Hack around that.
    with open('empty_audio_chunk', 'r') as in_f:
        empty_audio_chunk = in_f.read()

    while True:
        await ws_client.send(json.dumps({'audio_data': empty_audio_chunk}))
        await asyncio.sleep(50)


async def stream_transcripts(microphone_stream):
    auth_header = {"Authorization": f"{os.environ['ASSEMBLY_API_KEY']}" }
    url = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={microphone_stream.sample_rate}"
    
    async with websockets.connect(url, extra_headers=auth_header) as ws_client:
        async with asyncio.TaskGroup() as tg:

            tg.create_task(stream_audio_to_assembly(microphone_stream, ws_client))
            tg.create_task(session_heartbeat(ws_client))

            async for transcript in get_transcripts_from_websocket(ws_client):
                transcript = transcript.strip()
                if transcript != "":
                    yield transcript


async def main():
    with get_microphone_stream() as microphone_stream:
        async for transcript in stream_transcripts(microphone_stream):
            print(transcript)


if __name__ == "__main__":
    asyncio.run(main())