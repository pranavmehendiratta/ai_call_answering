
from whisper.Whisper import transcribeAudioFile
from ..gpt_helper.OpenAIChatGPT import ChatAgent
from audio.audio import BitsPerSample, Audio
from datetime import datetime
from tzlocal import get_localzone
from flask_sock import Sock
from eleven_labs.eleven_labs import ElevenLabs
from agents.role_playing_zero_shot_agent import direct_call_assistant

class AudioProcessing:
    def __init__(self, ws: Sock, steam_id: str):
        self._audio = Audio()

        self._chat_agent = ChatAgent()
        
        self._8_bit_audio_filename = "audio_8_bit.wav"

        self._16_bit_audio_filename = "audio_16_bit.wav"

        self._has_user_ever_spoken = False

        # Silence window duration in seconds
        self._silence_window_duration = 1

        # Current silence window length in chunks
        self._current_silence_window_length = 0

        # Length of silence window in chunks
        self._required_silence_window_length_in_chunks = int(self._silence_window_duration * self._audio._sample_rate / self._audio._chunk_size)

        # Eleven labs
        self._eleven_labs = ElevenLabs()

        # TODO: Probably don't need this
        self.socket = ws

        # TODO: Probably don't need this
        self.stream_id = steam_id
    
    def write(self, audio_bytes):
        is_speech = self._audio.write(audio_bytes)
        self._detect_silence_window(is_speech)

    def _detect_silence_window(self, is_speech):
        if is_speech:
            self._current_silence_window_length = 0
            self._has_user_ever_spoken = True
        else:
            self._current_silence_window_length += 1

        if self._current_silence_window_length == self._required_silence_window_length_in_chunks and self._has_user_ever_spoken:
            print(f"Processing Request @ {self._get_current_time()}, user stopped talking {self._silence_window_duration} seconds ago")
            transcript = self._transcribe()
            print(f"User: {transcript} @ {self._get_current_time()}")
            assistant_response = direct_call_assistant(transcript)
            self._eleven_labs.generate(assistant_response)
            #self._chat_agent.chat(transcript)
            #self.chunkAndSend(filename)
            #print(f"Bot: {response} @ {self._get_current_time()}")

    def _transcribe(self):
        self._audio.write_audio(BitsPerSample.EIGHT, "temp.wav")
        transcript = transcribeAudioFile("temp.wav")
        return transcript
        
    def write_audio(self, bits: BitsPerSample):
        filename = ""
        if bits == BitsPerSample.EIGHT:
            filename = self._8_bit_audio_filename
        elif bits == BitsPerSample.SIXTEEN:
            filename = self._16_bit_audio_filename

        self._audio.write_all_audio(bits, filename)

    def get_audio(self, bits: BitsPerSample):
        return self._audio.get_audio(bits)

    def _get_current_time(self):
        local_timezone = get_localzone()
        return datetime.now(local_timezone).strftime("%I:%M:%S.%f %p")