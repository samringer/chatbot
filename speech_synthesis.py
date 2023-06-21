import asyncio
import os
import httpx


VOICE_TO_ID = {
    "ScarJo": "gumL2npuufTINbbXVORo",
    "Gordon": "mRqr1hsq92w8OvxDaByz",
    "Morpheus": "v2XdYT3w2WLzRER3eb3W",
}


async def generate_speech_from_text(text: str = "A test", speaker: str = "ScarJo"):
    voice_id = VOICE_TO_ID[speaker]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {'xi-api-key': os.environ["ELEVEN_LABS_API_KEY"]}
    extra = {'json': {'text': text, 'model_id': 'eleven_monolingual_v1', 'voice_settings': None}}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url=url, headers=headers, timeout=500, **extra)
            audio = response.content
            if response.status_code != 200:
                raise RuntimeError(response.content)

        except httpx.ReadError:
            audio = ""
            

    
    return audio


if __name__ == "__main__":
    asyncio.run(generate_speech_from_text("This is a test"))
    

"""
To get list of available voices:
curl -X 'GET' \
  'https://api.elevenlabs.io/v1/voices' \
  --header 'accept: application/json' \
  --header "xi-api-key: $ELEVEN_LABS_API_TOKEN" | jq
"""
