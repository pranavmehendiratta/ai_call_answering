from pydub import AudioSegment

def convert_audio(raw_audio_data):
    # Step 1: Load the Audio
    audio = AudioSegment(
        raw_audio_data,
        sample_width=4,  # 32 bits = 4 bytes
        frame_rate=24000,
        channels=1
    )

    # Step 2: Change the Sample Rate
    audio = audio.set_frame_rate(8000)

    # Step 3: Change the Encoding
    # pydub uses strings like "pcm_u8" for 8-bit mu-law encoding.
    # Here we are converting it to mu-law and setting the sample width to 1 byte (8 bits).
    audio = audio.set_sample_width(1).set_channels(1).set_frame_rate(8000)

    # Convert audio format to pcm_mulaw
    audio.export("bark_generation_pcm.wav", format="s16le", codec="pcm_mulaw")


def main():
    audio = AudioSegment.from_wav("bark_generation.wav")
    raw_data = audio.raw_data
    convert_audio(raw_data)

if __name__ == "__main__":
    main()