import os
import sys
from google.cloud import speech_v1 as speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment

# Ensure the GOOGLE_APPLICATION_CREDENTIALS is set correctly
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sys.argv[1]  # Path to the JSON file

def convert_wav_to_mp3(wav_file):
    audio = AudioSegment.from_wav(wav_file)
    mp3_file = wav_file.replace(".wav", ".mp3")
    audio.export(mp3_file, format="mp3")
    return mp3_file

def split_audio(mp3_file, chunk_length_ms=60000):
    audio = AudioSegment.from_mp3(mp3_file)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_file = f"{mp3_file}_chunk{i}.mp3"
        chunk.export(chunk_file, format="mp3")
        chunk_files.append(chunk_file)
    return chunk_files

def transcribe_audio(mp3_file, language_code):
    client = speech.SpeechClient()
    with open(mp3_file, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=16000,
        language_code=language_code,
    )
    response = client.recognize(config=config, audio=audio)
    text = " ".join([result.alternatives[0].transcript for result in response.results])
    return text

def translate_text(text, target_language="en"):
    client = translate.Client()
    translation = client.translate(text, target_language=target_language)
    return translation["translatedText"]

def save_translation_to_file(translation, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(translation)

def main(audio_file, language_code):
    if audio_file.endswith(".wav"):
        mp3_file = convert_wav_to_mp3(audio_file)
        audio_file_type = "wav"
    else:
        mp3_file = audio_file
        audio_file_type = "mp3"

    chunk_files = split_audio(mp3_file)
    transcribed_text = ""
    for chunk_file in chunk_files:
        transcribed_text += transcribe_audio(chunk_file, language_code) + " "
        os.remove(chunk_file)  # Clean up the temporary chunk file

    if audio_file_type == "wav":
        os.remove(mp3_file)  # Clean up the temporary mp3 file if originally a wav file

    translated_text = translate_text(transcribed_text.strip(), "en")
    output_file = audio_file.replace(".mp3", "_translated.txt").replace(".wav", "_translated.txt")
    save_translation_to_file(translated_text, output_file)
    print(f"Translation saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py /path/to/service-account-file.json /path/to/audio/file language_code")
    else:
        audio_file = sys.argv[2]  # "path/to/your/song.mp3" or "path/to/your/song.wav"
        language_code = sys.argv[3]  # "de-DE"
        main(audio_file, language_code)
