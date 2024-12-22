import mido
import time
import os
import threading
import sounddevice as sd
import soundfile as sf
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
import soundcard as sc
import time

# Initialize variables
is_recording = False
midi_thread = None

# Load MIDI mapping from a CSV file
def load_midi_mapping(csv_file):
    mapping = {}
    with open(csv_file, newline='', mode='r') as f:
        reader = csv.reader(f)
        for row in reader:
            label, message_type, channel, control_or_note = row[:4]
            channel = int(channel.split('=')[-1])
            if message_type == 'note_on':
                note = int(control_or_note.split('=')[-1])
                mapping[(message_type, channel, note)] = label
            elif message_type == 'control_change':
                control = int(control_or_note.split('=')[-1])
                mapping[(message_type, channel, control)] = label
    return mapping

# Format MIDI messages using the mapping
def format_midi_message(message, timestamp, mapping):
    key = None
    if message.type == 'note_on' and message.velocity > 0:  # Only log when note_on is "pressed"
        key = (message.type, message.channel, message.note)
    elif message.type == 'control_change':
        key = (message.type, message.channel, message.control)
    
    if key and key in mapping:
        control_name = mapping[key]
        if message.type == 'note_on':
            action = 'pressed' if message.velocity > 0 else 'released'
            return f"{timestamp:.3f} seconds: {control_name} {action}, velocity {message.velocity}"
        elif message.type == 'control_change':
            return f"{timestamp:.3f} seconds: {control_name} adjusted, value {message.value}"
    else:
        return f"{timestamp:.3f} seconds: Unknown MIDI message {message}"

# Log MIDI messages to a file, skipping unknown entries
def log_midi_message(message, timestamp, log_file, mapping):
    log_entry = format_midi_message(message, timestamp, mapping)
    if "Unknown" not in log_entry:  # Only log if the message is not marked as Unknown
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')
    print(log_entry)

# Function to handle MIDI recording
def record_midi(log_file, mapping):
    global is_recording
    start_time = time.time()
    midi_input_port = mido.get_input_names()[0]
    
    try:
        with mido.open_input(midi_input_port) as inport:
            while is_recording:
                for message in inport.iter_pending():
                    timestamp = time.time() - start_time
                    log_midi_message(message, timestamp, log_file, mapping)
                time.sleep(0.01)  # Short sleep to prevent busy-waiting

    except Exception as e:
        print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    record_icon_path = "record_icon.png"  # Path to your recording icon image
    recording_region = (100, 100, 500, 500)  # Adjust coordinates to the recording button area

    while True:
        is_recording = detect_recording_icon(record_icon_path, region=recording_region)
        if is_recording:
            print("Rekordbox is currently recording!")
        time.sleep(1)  # Check every second


# PyQt5 GUI Application Class
class MidiRecorderApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the GUI layout
        self.setWindowTitle("MIDI and Audio Recorder")
        self.setGeometry(100, 100, 300, 150)

        # Create start and stop buttons
        self.start_button = QPushButton("Start Recording", self)
        self.stop_button = QPushButton("Stop Recording", self)
        self.status_label = QLabel("Press 'Start Recording' to begin.", self)

        # Connect buttons to functions
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)

        # Arrange layout
        layout = QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    # Start recording function
    def start_recording(self):
        global is_recording, midi_thread, audio_thread
        if not is_recording:
            is_recording = True
            log_file_path = os.path.join(os.getcwd(), 'midi_log.txt')
            
            # Start MIDI recording in a separate thread
            midi_thread = threading.Thread(target=record_midi, args=(log_file_path, midi_mapping))
            midi_thread.start()

            # Start audio recording in a separate thread
            audio_thread = threading.Thread(target=record_audio)
            audio_thread.start()

            self.status_label.setText("Recording MIDI and audio...")

    # Stop recording function
    def stop_recording(self):
        global is_recording
        if is_recording:
            is_recording = False
            midi_thread.join()  # Wait for the MIDI recording thread to finish
            audio_thread.join()  # Wait for the audio recording thread to finish
            self.status_label.setText("Recording stopped.")

# Run the PyQt5 application
if __name__ == "__main__":
    # Load the MIDI mapping from the CSV
    mapping_file = 'midi_mapping.csv'  # Adjust this path as needed
    midi_mapping = load_midi_mapping(mapping_file)
    
    app = QApplication([])
    window = MidiRecorderApp()
    window.show()
    app.exec_()
