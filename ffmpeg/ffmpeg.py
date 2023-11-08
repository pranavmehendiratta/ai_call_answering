import subprocess

class FFMpegInterface:
    def __init__(self):
        cmd = ['ffmpeg', '-i', 'pipe:0', '-acodec', 'pcm_mulaw', '-ar', '8000', '-ac', '1', 'pipe:1']
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def processMp3Bytes(self, mp3Bytes: bytes) -> bytes:
        print("Processing mp3 bytes")
        pcmBytes, _ = self.proc.communicate(mp3Bytes)
        print("Finished processing mp3 bytes")
        return pcmBytes