from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
import subprocess
import json
import base64
import os


class BarkHelper:
    def __init__(self):
        # download and load all models
        # preload_models()
        self.count = 0
        self.fileName = "tts/generated_audio/raw/bark_generation"
        self.pcmFileName = "tts/generated_audio/pcm/bark_generation"
        self.ext = ".wav"
        self.SPEAKER = "v2/en_speaker_6"

    def generate_audio(self, text: str):
        originalFilename = f"{self.fileName}_{self.count}{self.ext}"
        pcmFilename = f"{self.pcmFileName}_{self.count}{self.ext}"

        if os.path.exists(originalFilename):
            os.remove(originalFilename)
        if os.path.exists(pcmFilename):
            os.remove(pcmFilename)
            
        self.generate_audio_helper(text, originalFilename, pcmFilename)

    def generate_audio_helper(self, text: str, originalFilename, pcmFilename):
        print(f"Generating audio for: {text} using Bark")
        audio_array =  generate_audio(text, history_prompt=self.SPEAKER)
        write_wav(originalFilename, SAMPLE_RATE, audio_array)
        ffmpegCmd = ['ffmpeg', '-i', originalFilename, '-ar', '8000', '-ac', '1', '-acodec', 'pcm_mulaw', pcmFilename]
        subprocess.run(ffmpegCmd)
        self.send_audio(pcmFilename)
        self.count += 1

    
    def strip_metadata(self, filename):
        # Open the file in binary mode
        with open(filename, 'rb') as f:
            data = f.read()

        # Slice the data from the 59th byte to end, as header size is 58 bytes
        raw_audio = data[58:]

        # Print the first few bytes of raw audio for verification
        print(f'First few bytes of raw audio: {raw_audio[:10]}')
        
        return raw_audio

    def break_into_chunks(self, raw_audio):
        # Calculate the number of chunks
        num_chunks = len(raw_audio) // 160

        # Break the raw audio into 160 byte chunks
        chunks = [raw_audio[i*160:(i+1)*160] for i in range(num_chunks)]

        # If there are leftover bytes less than 160, append them as the last chunk
        if len(raw_audio) % 160 != 0:
            chunks.append(raw_audio[num_chunks*160:])

        return chunks

    def send_audio(self, filename):
        from TwilioIncomingModels import TwilioIncomingCall
        from settings import Settings
        settings = Settings()
        raw_audio = self.strip_metadata(filename)
        chunks = self.break_into_chunks(raw_audio) 
        connection: TwilioIncomingCall = settings.connections["test"]
        stream_id = connection.stream_id
        socket = connection.ws
        print(f"sending audio to {stream_id} from {filename}")
        for chunk in chunks:
            encoded_chunk = base64.b64encode(chunk).decode('utf-8')
            data = {
                "event": "media",
                "streamSid": stream_id,
                "media": {
                    "payload": encoded_chunk
                }
            }
            socket.send(json.dumps(data))

    
        
