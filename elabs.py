import os
import requests
import uuid

class Elabs():
    def __init__(self, key):
        self.BASE_URL = "https://api.elevenlabs.io/v1/"
        self.headers = {
            "xi-api-key": key,
            "Content-Type": "application/json"
        }

    def base_get(self, url):
        response = requests.get(self.BASE_URL + url, headers=self.headers)
        return response.json()

    def base_post(self, url, data):
        response = requests.post(self.BASE_URL + url, headers=self.headers, json=data)
        return response

    def get_models(self):
        return self.base_get("models")

    def get_voices(self):
        return self.base_get("voices")

    def tts(self, user_id, text, voice_id="21m00Tcm4TlvDq8ikWAM", model="eleven_monolingual_v1", similarity_boost=0.5, stability=0.5):
        CHUNK_SIZE = 1024

        data = {
            "text": text,
            "model": model,
            "voice_settings": {
                "similarity_boost": similarity_boost,
                "stability": stability
            }
        }

        print(data)

        response = self.base_post("text-to-speech/"+voice_id, data)
        print(response.status_code)
        if response.status_code != 200:
            print(response.json())
        filename = str(uuid.uuid1())+'.mp3'
        with open("./static/media/" + str(user_id) + '/' + filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        return {
            "url": "static/media/" + str(user_id) + "/" + filename
        }

    def tts_chuncked(self, user_id, text, voice_id="21m00Tcm4TlvDq8ikWAM", model="eleven_monolingual_v1", similarity_boost=0.5, stability=0.5):
        parts = []

        result = self.tts(user_id, text["intro"], voice_id, model, similarity_boost, stability)
        parts.append("./" + result["url"])

        for chapter in text["content"]:
            result = self.tts(user_id, chapter, voice_id, model, similarity_boost, stability)
            parts.append("./" + result["url"])

        result = self.tts(user_id, text["closure"], voice_id, model, similarity_boost, stability)
        parts.append("./"+result["url"])

        # get files in directory
        # files = os.listdir('static/media/' + str(user_id))
        # files = ["./static/media/"+ str(user_id) + "/" + file for file in files if file.endswith(".mp3")]

        return self.concatenate_audio_files(user_id=user_id, audio_files=parts)

    # funtion that receives a list of audio files urls and concatenates them
    def concatenate_audio_files(self, user_id, audio_files):
        CHUNK_SIZE = 1024

        filename = str(uuid.uuid1())+'.mp3'
        
        with open("./static/media/" + str(user_id) + '/' + filename, 'wb') as f:
            for audio_file in audio_files:
                with open(audio_file, 'rb') as af:
                    while True:
                        data = af.read(CHUNK_SIZE)
                        if not data:
                            break
                        f.write(data)
                # delete audio file
                os.remove(audio_file)

        return {
            "url": "static/media/" + str(user_id) + "/" + filename
        }