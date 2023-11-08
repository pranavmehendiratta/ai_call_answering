import struct
import webrtcvad
from enum import Enum

class BitsPerSample(Enum):
    EIGHT = 8
    SIXTEEN = 16

class AudioChunks:
    def __init__(self):
        # List of all 160 byte chunks of 8-bit PCM ULAW encoded audio or 320 byte chunks of 16-bit PCM decoded audio.
        # the type is controlled in Audio class. We don't need to know it here
        self._allBytes = []

        # Everytime a silence window is detected, we add the current chunk to this list.
        self._chunks = []

        # This is used to keep track of the current chunk from the end of last silence window
        self._currentChunkBytes = []

    def write(self, audio_bytes):
        self._allBytes.append(audio_bytes)
        self._currentChunkBytes.append(audio_bytes)

    def get_all_bytes(self):
        return b''.join(self._allBytes)

    def get_current_chunk_bytes(self):
        chunk = b''.join(self._currentChunkBytes)
        self._chunks.append(chunk)
        self._currentChunkBytes = []
        return chunk

class AudioChunks16Bit():
    def __init__(self):
        self._audio_chunks = AudioChunks()

        # Tracks if the chunk is speech or not. Idk if we need this. 
        # Only available for 16-bit decoded audio. Look at the write method below.
        self._all_is_speech = []

    def write(self, is_speech, audio_bytes):
        self._all_is_speech.append(is_speech)
        self._audio_chunks.write(audio_bytes)

    def get_all_bytes(self):
        return self._audio_chunks.get_all_bytes()

    def get_current_chunk_bytes(self):
        return self._audio_chunks.get_current_chunk_bytes()

class AudioChunks8Bit():
    def __init__(self):
        self._audio_chunks = AudioChunks()

    def write(self, audio_bytes):
        self._audio_chunks.write(audio_bytes)

    def get_all_bytes(self):
        return self._audio_chunks.get_all_bytes()

    def get_current_chunk_bytes(self):
        return self._audio_chunks.get_current_chunk_bytes()

# This class should be updated to support only a single stream type. And those types should be both
# for the input audio from twilio and the output audio from eleven labs.
class Audio:
    def __init__(self):
        self._num_of_channels = 1

        # Number of samples per second could be 8000, 16000, 44.1KHz. For us, its always 8000.
        self._sample_rate = 8000

        # This hold 8-bit PCM ULAW encoded bytes. Each chunk is 160 bytes long and contains 20ms of audio data.
        self._8_bit_pcm_ulaw_encoded_bytes = AudioChunks8Bit()

        # This hold 16-bit PCM decoded bytes. Each chunk is 320 bytes long and contains 20ms of audio data.
        self._16_bit_pcm_decoded_bytes = AudioChunks16Bit()

        # For speech detection
        self._vad = webrtcvad.Vad(3)

        # Chunk size in bytes for 8-bit PCM ULAW encoded audio. Each chunk is 160 bytes long and contains 20ms of audio data.
        self._chunk_size = 160

        # Time length since start of the call in seconds
        self.duration = 0

    def write(self, audio_bytes):
        # Raw audio - sending this directly to whisper for transcription. Using this instead of decoded audio because the size if half.
        self._8_bit_pcm_ulaw_encoded_bytes.write(audio_bytes)

        # Decoded audio - using this for real-time speech detection.
        decoded_bytes = self._decode_8_bit_pcm_ulaw_encoded_bytes(audio_bytes)

        # Detect speech
        is_speech = self._vad.is_speech(decoded_bytes, self._sample_rate)

        self.duration += 0.02 # 20ms

        # Keep track of decoded audio for verification purposes.
        self._16_bit_pcm_decoded_bytes.write(is_speech, decoded_bytes)

        return is_speech
    
    def _decode_8_bit_pcm_ulaw_encoded_bytes(self, audio_bytes):
        output_data = []
        for byte in audio_bytes:
            decoded_byte = self._mulaw_decode(byte)
            output_data.append(struct.pack('<h', decoded_byte))
        output_data_bytes = b''.join(output_data)
        return output_data_bytes

    def _mulaw_decode(self, number):
        MULAW_BIAS = 33
        sign = 0
        position = 0
        decoded = 0

        number = ~number  # Bitwise complement of number

        if number & 0x80:  # Check if the MSB (Most Significant Bit) is set
            number &= ~(1 << 7)  # Clear the MSB
            sign = -1  # Set sign to negative

        position = ((number & 0xF0) >> 4) + 5  # Extract the position bits and calculate position

        # Perform decoding
        decoded = ((1 << position) | ((number & 0x0F) << (position - 4)) | (1 << (position - 5))) - MULAW_BIAS

        decoded = decoded % 65536  # Enforce 2-byte unsigned range (0 to 65535)

        if sign == 0:
            return decoded
        else:
            return -decoded

    def write_all_audio(self, bits: BitsPerSample, filename: str):
        with open(filename, "wb") as file:
            file.write(b'RIFF')
            
            audio_data = b''
            if bits == BitsPerSample.EIGHT:
                audio_data = self._8_bit_pcm_ulaw_encoded_bytes.get_all_bytes()
            elif bits == BitsPerSample.SIXTEEN:
                audio_data = self._16_bit_pcm_decoded_bytes.get_all_bytes()

            audio_data_length = len(audio_data)
            num_of_channels = 1

            if bits == BitsPerSample.SIXTEEN:
                audioformat = 1
                file.write(
                    struct.pack(
                        '<L4s4sLHHLLHH4s', # Format
                        36 + audio_data_length, b'WAVE', b'fmt ', 16,
                        audioformat, num_of_channels, self._sample_rate,
                        int(num_of_channels * self._sample_rate * (bits.value / 8)),
                        int(num_of_channels * (bits.value / 8)), bits.value, b'data'
                    )
                )
            elif bits == BitsPerSample.EIGHT:
                audioformat = 7
                file.write(
                    struct.pack(
                        '<L4s4sLHHLLHHH4sLL4s', # Format
                        50 + audio_data_length, b'WAVE', b'fmt ', 18,
                        audioformat, num_of_channels, self._sample_rate,
                        int(num_of_channels * self._sample_rate * (bits.value/8)),
                        int(num_of_channels * (bits.value / 8)), bits.value, 0, b'fact', 4, 
                        audio_data_length, b'data'
                    )
                )

            file.write(struct.pack('<L', audio_data_length))
            file.write(audio_data)

    # Write the current chunk to the file and reset the chunk
    def write_audio(self, bits: BitsPerSample, filename: str):
        with open(filename, "wb") as file:
            file.write(b'RIFF')
            
            audio_data = b''
            if bits == BitsPerSample.EIGHT:
                audio_data = self._8_bit_pcm_ulaw_encoded_bytes.get_current_chunk_bytes()
            elif bits == BitsPerSample.SIXTEEN:
                audio_data = self._16_bit_pcm_decoded_bytes.get_current_chunk_bytes()

            audio_data_length = len(audio_data)
            num_of_channels = 1

            if bits == BitsPerSample.SIXTEEN:
                audioformat = 1
                file.write(
                    struct.pack(
                        '<L4s4sLHHLLHH4s', # Format
                        36 + audio_data_length, b'WAVE', b'fmt ', 16,
                        audioformat, num_of_channels, self._sample_rate,
                        int(num_of_channels * self._sample_rate * (bits.value / 8)),
                        int(num_of_channels * (bits.value / 8)), bits.value, b'data'
                    )
                )
            elif bits == BitsPerSample.EIGHT:
                audioformat = 7
                file.write(
                    struct.pack(
                        '<L4s4sLHHLLHHH4sLL4s', # Format
                        50 + audio_data_length, b'WAVE', b'fmt ', 18,
                        audioformat, num_of_channels, self._sample_rate,
                        int(num_of_channels * self._sample_rate * (bits.value/8)),
                        int(num_of_channels * (bits.value / 8)), bits.value, 0, b'fact', 4, 
                        audio_data_length, b'data'
                    )
                )

            file.write(struct.pack('<L', audio_data_length))
            file.write(audio_data)