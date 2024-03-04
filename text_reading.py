import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QInputDialog
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QTimer
from pygame import mixer
from config import get_file_path
import pickle
from pathlib import Path
from difflib import SequenceMatcher

def similarity(a, b):
    """Compute the similarity score between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def map_transcribed_to_original(transcription, original_segments):
    mapping = []
    j = 0  # Index for original_segments

    for i in range(len(transcription)):
        if j >= len(original_segments) - 1:
            # If we are at the last original segment, assign all remaining transcribed words to it
            mapping.append((transcription[i]['word'], original_segments[j]))
            continue

        # Calculate similarity scores
        current_similarity = similarity(transcription[i]['word'], original_segments[j])
        next_similarity = similarity(transcription[i]['word'], original_segments[j + 1])

        if next_similarity > current_similarity:
            j += 1  # Move to the next original segment if it's a closer match

        mapping.append((transcription[i]['word'], original_segments[j]))

    return mapping


class AudioTextSyncApp(QWidget):
    def __init__(self, transcription, original_text, name):
        super().__init__()
        self.transcription = sorted(transcription, key=lambda x: x['start'])
        self.original_text_segments = self.segment_original_text(original_text)
        self.current_segment_index = 0
        self.name = name
        self.buffer_time = 0.1  # 1/10 of a second buffer
        self.initUI()
        self.initAudio()
        self.mapping = map_transcribed_to_original(self.transcription, self.original_text_segments)
        self.last_printed_original_word = None

        

    def initUI(self):
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Audio-Text Synchronization')
        
        layout = QVBoxLayout()

        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)  # Make the QTextEdit read-only
        self.textEdit.setStyleSheet("font-size: 16pt;")
        layout.addWidget(self.textEdit)

        playButton = QPushButton('Play', self)
        playButton.clicked.connect(self.playAudio)
        layout.addWidget(playButton)

        self.setLayout(layout)

    def initAudio(self):
        mixer.init()
        self.audio_path = get_file_path('audios', self.name, 'mp3')  # Using the centralized file path function
        mixer.music.load(str(self.audio_path))  # Convert Path object to string


    def playAudio(self):
        mixer.music.play()
        self.checkPlayback()
    
    def checkPlayback(self):
        if not mixer.music.get_busy():
            self.updateTimer.stop()  # Stop the timer if audio has stopped playing
            return

        current_time = mixer.music.get_pos() / 1000.0  # Current playback time in seconds
        
        # Find the last transcribed entry whose start time is less than the current playback time
        while self.current_segment_index < len(self.transcription) and self.transcription[self.current_segment_index]['start'] <= current_time:
            transcribed_word = self.transcription[self.current_segment_index]['word']
            original_word = self.mapping[self.current_segment_index][1]  # Assuming mapping is (transcribed_word, original_word)
            
            # Check if the original word has changed since the last print
            if original_word != self.last_printed_original_word:
                # Print the words to the terminal for verification
                print(f"Original: {original_word} | Transcribed: {transcribed_word}")
                self.last_printed_original_word = original_word  # Update the last printed word

            self.current_segment_index += 1
        
        # Update the UI to display the current original word or segment
        if self.current_segment_index < len(self.mapping):
            # Generate the text to display based on the unique original words printed
            unique_original_words = [pair[1] for i, pair in enumerate(self.mapping[:self.current_segment_index + 1]) if i == 0 or self.mapping[i-1][1] != pair[1]]
            text_to_display = " ".join(unique_original_words)
            self.textEdit.setPlainText(text_to_display)
            self.textEdit.moveCursor(QTextCursor.End)  # Scroll to the end of the text

        QTimer.singleShot(10, self.checkPlayback)  # Schedule the next check


            
        
    def segment_original_text(self, text):
        # Split the text into lines to preserve new lines, then split each line by spaces.
        lines = text.split('\n')
        segments = []
        for line in lines[:-1]:  # Exclude the last line from adding a new line segment after it
            line_segments = line.split()  # Split each line into words and punctuation
            if line_segments:  # Check if there are any segments to avoid index errors
                line_segments[-1] += '\n'  # Merge newline character with the last word of the line
            segments.extend(line_segments)
        # Add segments from the last line without appending a new line segment
        segments.extend(lines[-1].split())
        return segments


    def displaySegment(self, text):
        self.textEdit.setPlainText(text)  # Update the displayed text
        self.textEdit.moveCursor(QTextCursor.End)  # Scroll to the end of the text

def get_available_combinations(texts_path, audios_path, transcripts_path):
    text_files = {p.stem for p in texts_path.glob('*.txt')}
    audio_files = {p.stem for p in audios_path.glob('*.mp3')}
    transcript_files = {p.stem for p in transcripts_path.glob('*.pkl')}

    # Get the intersection of text, audio, and transcript files
    return list(text_files & audio_files & transcript_files)


def load_transcript_and_text(name):
    text_file_path = get_file_path('texts', name, 'txt')
    transcript_file_path = get_file_path('transcripts', name, 'pkl')

    with open(text_file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()

    with open(transcript_file_path, 'rb') as file:
        transcript = pickle.load(file)

    return transcript, text_content

def select_combination(combinations):
    item, ok = QInputDialog.getItem(
        None, "Select Combination", "Available Combinations:", combinations, 0, False
    )
    if ok and item:
        return item
    return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    texts_path = get_file_path('texts', '')
    audios_path = get_file_path('audios', '')
    transcripts_path = get_file_path('transcripts', '')
    
    combinations = get_available_combinations(texts_path, audios_path, transcripts_path)
    if not combinations:
        print("No available text/audio/transcript combinations found.")
        sys.exit(1)
        
    name = select_combination(combinations)
    if not name:
        print("No combination selected.")
        sys.exit(1)

    transcript, text_content = load_transcript_and_text(name)

    ex = AudioTextSyncApp(transcript.words, text_content, name)
    ex.show()
    sys.exit(app.exec_())