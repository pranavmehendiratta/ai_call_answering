from typing import Dict
from audio.audio_processing import AudioProcessing
from flask_sock import Sock
import os

class TwilioIncomingCall:
    def __init__(self, stream_id: str, account_id: str, call_id: str, first_name: str, last_name: str, ws: Sock):
        self.stream_id = stream_id
        self.account_id = account_id
        self.call_id = call_id
        self.first_name = first_name
        self.last_name = last_name
        self.ws = ws
        self.audio = AudioProcessing(ws, stream_id)

    @classmethod
    def fromStartEvent(cls, data: Dict, ws: Sock) -> 'TwilioIncomingCall':
        start_info = data.get('start', {})
        custom_params = start_info.get('customParameters', {})

        return cls(
            stream_id=data.get('streamSid', ''),
            account_id=start_info.get('accountSid', ''),
            call_id=start_info.get('callSid', ''),
            first_name=custom_params.get('FirstName', ''),
            last_name=custom_params.get('LastName', ''),
            ws=ws
        )
    
    def send_intro_audio(self):
        self.audio._eleven_labs.send_audio(filename = f"{os.getenv('ELEVEN_LABS_AUDIO_DIR')}/intro_pcm_audio_0.wav")
    
    def handleMediaBytes(self, chunk: bytes):
        self.audio.write(chunk)

    def __str__(self) -> str:
        return f"TwilioIncomingCall(stream_id={self.stream_id}, account_id={self.account_id}, call_id={self.call_id}, first_name={self.first_name}, last_name={self.last_name})"
    

