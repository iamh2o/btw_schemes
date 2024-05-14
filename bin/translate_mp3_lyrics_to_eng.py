import os
import sys
import shutil
import logging
from google.cloud import speech_v1 as speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Ensure the GOOGLE_APPLICATION_CREDENTIALS is set correctly
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sys.argv[1]  # Path to the JSON file

def convert_wav_to_mp3(wav_file):
    logger.info(f"Converting WAV to MP3: {wav_file}")
    audio = AudioSegment.from_wav(wav_file)
    mp3_file = wav_file.replace(".wav", ".mp3")
    audio.export(mp3_file, format="mp3")
    logger.info(f"Conversion complete: {mp3_file}")
    return mp3_file

def split_audio(mp3_file, chunk_length_ms=60000):
    logger.info(f"Splitting audio file into chunks: {mp3_file}")
    audio = AudioSegment.from_mp3(mp3_file)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_file = f"{mp3_file}_chunk{i}.mp3"
        chunk.export(chunk_file, format="mp3")
        chunk_files.append(chunk_file)
    logger.info(f"Created {len(chunk_files)} chunks")
    return chunk_files

def transcribe_audio(mp3_file, language_code):
    logger.info(f"Transcribing audio chunk: {mp3_file}")
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
    logger.info(f"Transcription complete for chunk: {mp3_file}")
    return text

def translate_text(text, target_language="en"):
    logger.info("Translating text")
    client = translate.Client()
    translation = client.translate(text, target_language=target_language)
    logger.info("Translation complete")
    return translation["translatedText"]

def save_translation_to_file(translation, output_file):
    logger.info(f"Saving translation to file: {output_file}")
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(translation)
    logger.info("Translation saved successfully")

def main(audio_file, language_code, output_dir, save_temp):
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

    if audio_file_type == "wav" and save_temp.upper() == "Y":
        temp_dir = os.path.join(os.path.dirname(mp3_file), 'tempfiles')
        os.makedirs(temp_dir, exist_ok=True)
        shutil.copy(mp3_file, output_dir)
        logger.info(f"Temporary MP3 file saved to: {temp_dir}")
        os.remove(mp3_file)  # Clean up the temporary mp3 file if originally a wav file

    translated_text = translate_text(transcribed_text.strip(), "en")
    output_file = os.path.join(output_dir, os.path.basename(audio_file).replace(".mp3", "_translated.txt").replace(".wav", "_translated.txt"))
    save_translation_to_file(translated_text, output_file)
    logger.info(f"Translation saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        logger.error("Usage: python script.py /path/to/service-account-file.json /path/to/audio/file language_code /path/to/output/directory Y/N")
    else:
        audio_file = sys.argv[2]  # "path/to/your/song.mp3" or "path/to/your/song.wav"
        language_code = sys.argv[3]  # "de-DE"
        output_dir = sys.argv[4]  # Path to the output directory
        save_temp = sys.argv[5]  # 'Y' or 'N' indicating whether to save a copy of the temporary MP3 file
        main(audio_file, language_code, output_dir, save_temp)
