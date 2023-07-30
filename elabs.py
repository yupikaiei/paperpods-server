import os
import requests
import uuid

BASE_URL = url = "https://api.elevenlabs.io/v1/"
API_KEY = os.getenv("ELEVENLABS_API_KEY")

headers = {
  "Accept": "application/json",
  "xi-api-key": API_KEY
}

def base_get(url):
    global BASE_URL
    global headers

    response = requests.get(BASE_URL + url, headers=headers)
    return response.json()

def base_post(url, data):
    global BASE_URL
    global headers

    response = requests.post(BASE_URL + url, headers=headers, json=data)
    return response

def get_models():
    return base_get("models")

def get_voices():
    return base_get("voices")

def tts(user_id, text, voice_id="21m00Tcm4TlvDq8ikWAM", model="eleven_monolingual_v1", similarity_boost=0.5, stability=0.5):
    CHUNK_SIZE = 1024

    data = {
        "text": text,
        "model": model,
        "voice_settings": {
            "similarity_boost": similarity_boost,
            "stability": stability
        }
    }

    response = base_post("text-to-speech/"+voice_id, data)
    filename = str(uuid.uuid1())+'.mp3'
    with open("static/media/" + user_id + '/' + filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)

    return {
        "url": "http://localhost:3000/static/media/" + user_id + "/" + filename
    }