from elevenlabs import generate, play, save, stream
import subprocess
import struct
import os
import json
import base64
from datetime import datetime
from tzlocal import get_localzone

class ElevenLabs:
    def __init__(self):
        self._sentence_num = 0
        self._voice = "Bella"
        self._model="eleven_monolingual_v1"
        self._count = 0
        self.count = 0
        self.intro_file_name = os.getenv("ELEVEN_LABS_INTRO_AUDIO_PATH") 
        self.intro_pcm_file_name = os.getenv("ELEVEN_LABS_INTRO_PCM_AUDIO_PATH")
        self.fileName = os.getenv("ELEVEN_LABS_AUDIO_FILE_PATH")
        self.pcmFileName = os.getenv("ELEVEN_LABS_PCM_AUDIO_FILE_PATH")
        self.ext = ".wav"

    def generate(self, text: str):
        originalFilename = f"{self.fileName}_{self.count}{self.ext}"
        pcmFilename = f"{self.pcmFileName}_{self.count}{self.ext}"
        self._generate(text, originalFilename, pcmFilename)
        self.count += 1

    def _generate(
        self,
        text: str,
        original_filename: str,
        pcm_filename: str
    ): 
        print(f"Generating audio for: {text}")
        if os.path.exists(original_filename):
            os.remove(original_filename)
        if os.path.exists(pcm_filename):
            os.remove(pcm_filename)

        print(f"Started generating audio @ {self.get_current_time()}")
        audio = generate(
            text = text,
            voice = self._voice,
            model = self._model
        )
        save(audio, original_filename)
        print(f"Done generating audio @ {self.get_current_time()}. Starting ffmpeg conversion")
        ffmpegCmd = ['ffmpeg', '-i', original_filename, '-ar', '8000', '-ac', '1', '-acodec', 'pcm_mulaw', pcm_filename]
        subprocess.run(ffmpegCmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"Done converting audio @ {self.get_current_time()}. Starting to send audio")
        self.send_audio(pcm_filename)
        print(f"Done sending audio @ {self.get_current_time()}")

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
        from settings import shared_connections
        print("Inside send_audio")
        print(f"filename: {filename}")
        raw_audio = self.strip_metadata(filename)
        chunks = self.break_into_chunks(raw_audio) 
        print("Done breaking into chunks")
        print("shared_connections: ", shared_connections)
        connection: TwilioIncomingCall = shared_connections["test"]
        print(f"connection: {connection}")
        stream_id = connection.stream_id
        socket = connection.ws
        print(f"stream_id: {stream_id}")
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

        mark = {
            "event": "mark",
            "streamSid": stream_id,
            "mark": {
                "name": f"done sending chunk = {self.count}"  
            }
        }

        socket.send(json.dumps(data))

    def generate_stream(self, text: str):
        print(f"Generating audio stream for: {text} \n<END>")
        audio_stream = generate(
            text = text,
            voice = self._voice,
            model = self._model,
            stream = True
        )
        self._sentence_num += 1
        sentence_bytes = b''
        ffmpeg_bytes = b''
        chunkNum = 0
        for chunk in audio_stream:
            chunkNum += 1
            if chunk is not None:
                #print(f"chunk num = {chunkNum}, chunk size: {len(chunk)}")
                sentence_bytes += chunk
                pcm_encoded_bytes = self.ffmpeg.processMp3Bytes(chunk)
                #ffmpeg_bytes += pcm_encoded_bytes
                #print(f"chunk num = {chunkNum}, chunk size = {len(chunk)}  pcm_encoded_bytes size: {len(pcm_encoded_bytes)}")
                print(f"chunk num = {chunkNum}, chunk size = {len(chunk)}")
        save(sentence_bytes, f"eleven_labs/audio_files/eleven_labs_helper_stream_testi-{self._sentence_num}.mp3")
        #self.write_audio(ffmpeg_bytes, f"eleven_labs/audio_files/eleven_labs_helper_stream_testi-{self._sentence_num}-8-bit.wav")

    # Write the current chunk to the file and reset the chunk
    def write_audio(self, audio_data: bytes, filename: str):
        with open(filename, "wb") as file:
            file.write(b'RIFF')
            audio_data_length = len(audio_data)
            num_of_channels = 1

            audioformat = 7
            file.write(
                struct.pack(
                    '<L4s4sLHHLLHHH4sLL4s', # Format
                    50 + audio_data_length, b'WAVE', b'fmt ', 18,
                    audioformat, num_of_channels, self._sample_rate,
                    int(num_of_channels * self._sample_rate * (8/8)),
                    int(num_of_channels * (8 / 8)), 8, 0, b'fact', 4, 
                    audio_data_length, b'data'
                )
            )

            file.write(struct.pack('<L', audio_data_length))
            file.write(audio_data)

    def get_current_time(self):
        local_timezone = get_localzone()
        return datetime.now(local_timezone).strftime("%I:%M:%S.%f %p")
    

    def generate_intro_audio(
        self, 
        text: str,
    ) -> None:
        originalFilename = f"{self.intro_file_name}_{self.count}{self.ext}"
        pcmFilename = f"{self.intro_pcm_file_name}_{self.count}{self.ext}"
        self._generate(text, originalFilename, pcmFilename)
        self.count += 1

"""
eleven_labs = ElevenLabs()
eleven_labs.generate_intro_audio(
    text = "Hello, this is John at Timeplated Restaurant. How may I help you?",
)
print("Done generating audio")
"""