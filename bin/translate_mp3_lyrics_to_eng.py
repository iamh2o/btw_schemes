import os
import shutil
import logging
import argparse
from google.cloud import speech_v1 as speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def convert_wav_to_mp3(wav_file, output_dir):
    logger.info(f"Converting WAV to MP3: {wav_file}")
    audio = AudioSegment.from_wav(wav_file)
    mp3_file = os.path.join(output_dir, os.path.basename(wav_file).replace(".wav", ".mp3"))
    audio.export(mp3_file, format="mp3")
    logger.info(f"Conversion complete: {mp3_file}")
    return mp3_file

def split_audio(mp3_file, output_dir, chunk_length_ms=60000):
    logger.info(f"Splitting audio file into chunks: {mp3_file}")
    audio = AudioSegment.from_mp3(mp3_file)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_file = os.path.join(output_dir, f"{os.path.basename(mp3_file)}_chunk{i}.mp3")
        chunk.export(chunk_file, format="mp3")
        chunk_files.append(chunk_file)
    logger.info(f"Created {len(chunk_files)} chunks")
    return chunk_files

def transcribe_audio(mp3_file, language_code=None, offset=0):
    logger.info(f"Transcribing audio chunk: {mp3_file}")
    client = speech.SpeechClient()
    with open(mp3_file, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=16000,
        language_code=language_code if language_code else "en-US",
        enable_word_time_offsets=True
    )
    response = client.recognize(config=config, audio=audio)

    transcriptions = []
    for result in response.results:
        for alternative in result.alternatives:
            for word_info in alternative.words:
                transcriptions.append((word_info.start_time.total_seconds() + offset, word_info.word))
    
    logger.info(f"Transcription complete for chunk: {mp3_file} with {len(transcriptions)} words")
    return transcriptions

def translate_text_preserve_newlines(text, target_language="en"):
    logger.info("Translating text with newlines preserved")
    client = translate.Client()
    text = text.replace("\n\n", " [NEWLINE] ")
    translation = client.translate(text, target_language=target_language)
    translated_text = translation["translatedText"].replace(" [NEWLINE] ", "\n\n")
    logger.info("Translation complete")
    return translated_text

def detect_language(text):
    logger.info("Detecting language")
    client = translate.Client()
    detection = client.detect_language(text)
    detected_language = detection['language']
    logger.info(f"Detected language: {detected_language}")
    return detected_language

def save_translation_to_file(translation, output_file):
    logger.info(f"Saving translation to file: {output_file}")
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(translation)
    logger.info("Translation saved successfully")

def main(config_file, audio_file, language_code, output_dir, save_temp, overwrite_translation, pause_seconds):
    # Ensure the GOOGLE_APPLICATION_CREDENTIALS is set correctly
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config_file

    output_file = os.path.join(output_dir, os.path.basename(audio_file).replace(".mp3", "_translated.txt").replace(".wav", "_translated.txt"))

    if os.path.exists(output_file) and overwrite_translation.upper() == "N":
        logger.warning(f"Output file already exists: {output_file}")
        sys.exit(1)
    
    if not output_dir.endswith('/'):
        logger.warning("Output directory must end with a '/'")
        output_dir += '/'
    
    if not os.path.exists(audio_file):
        logger.error(f"Audio file does not exist: {audio_file}")
        sys.exit(1)
    
    if not os.path.exists(config_file):
        logger.error(f"Config file does not exist: {config_file}")
        sys.exit(1)
        
    if not os.path.exists(output_dir):
        logger.error(f"Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    if audio_file.endswith(".wav"):
        mp3_file = convert_wav_to_mp3(audio_file, output_dir)
        audio_file_type = "wav"
    else:
        mp3_file = audio_file
        audio_file_type = "mp3"

    chunk_files = split_audio(mp3_file, output_dir)
    transcriptions = []
    word_counts = []
    detected_language = None

    for i, chunk_file in enumerate(chunk_files):
        chunk_transcriptions = transcribe_audio(chunk_file, language_code, offset=i * 60)
        transcriptions.extend(chunk_transcriptions)
        if not language_code and i == 0 and chunk_transcriptions:  # Detect language using the first chunk if not provided
            detected_language = detect_language(" ".join(word for _, word in chunk_transcriptions))
            language_code = detected_language
        
        word_counts.append(len(chunk_transcriptions))
        os.remove(chunk_file)  # Clean up the temporary chunk file after processing

    # Sort transcriptions by timestamp
    transcriptions.sort()

    transcribed_text = ""
    for i in range(len(transcriptions)):
        timestamp, word = transcriptions[i]
        if i > 0 and timestamp - transcriptions[i - 1][0] > pause_seconds:
            transcribed_text += "\n\n"
        transcribed_text += f"{word} "
    
    if transcriptions:
        transcribed_text += "\n\n"  # Add two newlines after the last word

    if audio_file_type == "wav" and save_temp.upper() == "Y":
        temp_dir = os.path.join(output_dir, 'tempfiles')
        os.makedirs(temp_dir, exist_ok=True)
        shutil.copy(mp3_file, temp_dir)
        logger.info(f"Temporary MP3 file saved to: {temp_dir}")
        os.remove(mp3_file)  # Clean up the temporary mp3 file if originally a wav file

    translated_text = translate_text_preserve_newlines(transcribed_text.strip(), "en")
    save_translation_to_file(translated_text, output_file)
    logger.info(f"Translation saved to {output_file}")

    logger.info(f"File name: {os.path.basename(audio_file)}")
    logger.info(f"Source language: {language_code}")
    logger.info(f"Number of chunks: {len(chunk_files)}")
    for i, count in enumerate(word_counts):
        logger.info(f"Words in chunk {i}: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe and translate audio files.")
    parser.add_argument("-c", "--config", required=True, help="Path to the Google service account JSON file")
    parser.add_argument("-f", "--file", required=True, help="Path to the audio file (MP3 or WAV)")
    parser.add_argument("-l", "--lang", help="Language code of the audio file (e.g., 'de'), if not provided, the language will be detected <-- but not reliably!")
    parser.add_argument("-o", "--out-dir", required=True, help="Path to the output directory (must end with '/')")
    parser.add_argument("-s", "--save-mp3", default="N", help="Save a copy of the temporary MP3 file if input is WAV ('Y' or 'N', default is 'N')")
    parser.add_argument("-x", "--overwrite-translation", default="N", help="Overwrite translation txt file if it already exists ('Y' or 'N', default is 'N')")
    parser.add_argument("-p", "--pause", type=float, default=2, help="Number of seconds pause between words after which to insert a newline (default is 2 seconds)")

    args = parser.parse_args()
    
    if not os.path.exists(args.out_dir):
        logger.error(f"Output directory does not exist: {args.out_dir}")
        sys.exit(1)
    
    if not os.path.exists(args.config):
        logger.error(f"Config file does not exist: {args.config}")
        sys.exit(1)
        
    if not os.path.exists(args.file):
        logger.error(f"Audio file does not exist: {args.file}")
        sys.exit(1)
    
    main(args.config, args.file, args.lang, args.out_dir, args.save_mp3, args.overwrite_translation, args.pause)
