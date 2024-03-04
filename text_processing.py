from config import client, get_file_path
from pydub import AudioSegment
import pickle

def get_unprocessed_files(text_dir, audio_dir):
    """Get a list of text files that have not been processed to audio."""
    unprocessed_files = []
    for text_file in text_dir.iterdir():
        if text_file.is_file() and text_file.suffix == '.txt':
            audio_file = audio_dir / text_file.with_suffix('.mp3').name
            if not audio_file.exists():
                unprocessed_files.append(text_file.stem)
    return unprocessed_files

def confirm_processing(file_list):
    """Ask user to confirm processing of files."""
    if not file_list:
        print("All files have already been processed.")
        return None
    elif len(file_list) == 1:
        response = input(f"One file to process: {file_list[0]}. Process this file? (y/n) ")
        return file_list[0] if response.lower() == 'y' else None
    else:
        for i, file_name in enumerate(file_list, 1):
            print(f"{i}. {file_name}")
        selected = int(input("Select a file to process by number: "))
        return file_list[selected - 1]

def split_text(text, max_length=4096):
    """Split text into chunks without splitting words, each not exceeding max_length."""
    words = text.split()
    chunks = []
    current_chunk = words[0]

    for word in words[1:]:
        if len(current_chunk) + len(word) + 1 <= max_length:
            current_chunk += " " + word
        else:
            chunks.append(current_chunk)
            current_chunk = word
    chunks.append(current_chunk)  # Add the last chunk
    return chunks

def process_text_chunks(input_file_name, output_folder):
    text_file_path = get_file_path('texts', input_file_name, 'txt')
    output_file_path = get_file_path('audios', input_file_name, 'mp3')

    with open(text_file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()

    chunks = split_text(text_content)
    combined_audio = AudioSegment.empty()

    for i, chunk in enumerate(chunks):
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=chunk
        )

        # Save each audio segment to a temporary file
        temp_audio_path = get_file_path('temp', f"temp_segment_{i}", 'mp3')
        response.stream_to_file(str(temp_audio_path))  # Convert Path object to string

        # Load the temporary audio file and append it to the combined audio
        segment = AudioSegment.from_mp3(str(temp_audio_path))
        combined_audio += segment

        # Remove the temporary file
        temp_audio_path.unlink()

    # Save the combined audio to the final MP3 file
    combined_audio.export(str(output_file_path), format="mp3")

def transcribe_audio(file_name):
    """Transcribes the audio file and saves the transcript."""
    audio_file_path = get_file_path('audios', file_name, 'mp3')
    transcript_file_path = get_file_path('transcripts', file_name, 'pkl')

    with open(audio_file_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

    # Pickle the object and save it to a file
    with open(transcript_file_path, 'wb') as file:
        pickle.dump(transcript, file)

    print(f"Transcript object pickled and saved to {transcript_file_path}")

# Paths
texts_path = get_file_path('texts', '')
audios_path = get_file_path('audios', '')

# Find unprocessed files
unprocessed_files = get_unprocessed_files(texts_path, audios_path)
file_to_process = confirm_processing(unprocessed_files)

# Process the selected file
if file_to_process:
    process_text_chunks(file_to_process, audios_path)
    print(f"Processed {file_to_process}.mp3")
    # After processing the audio file, transcribe it
    transcribe_audio(file_to_process)
