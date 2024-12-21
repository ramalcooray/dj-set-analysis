import mido
import time
import os
import threading
import sounddevice as sd
import soundfile as sf
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

# Initialize variables
is_recording = False
midi_thread = None
audio_thread = None
audio_filename = "audio_output.wav"

# # Example MIDI mapping (Adjust based on your controller)
# MIDI_MAPPING = {
#     'note_on': {
#         60: 'Play Button',
#         61: 'Cue Button',
#     },
#     'control_change': {
#         16: 'Volume Fader',
#         17: 'EQ Low Knob',
#     },
#     'pitchwheel': 'Jog Wheel'
# }

# # Function to format MIDI messages
# def format_midi_message(message, timestamp):
#     if message.type == 'note_on' or message.type == 'note_off':
#         control_name = MIDI_MAPPING.get('note_on', {}).get(message.note, 'Unknown Button')
#         action = 'pressed' if message.velocity > 0 else 'released'
#         return f"{timestamp:.3f} seconds: Button ({control_name}) {action}, velocity {message.velocity}"
    
#     elif message.type == 'control_change':
#         control_name = MIDI_MAPPING.get('control_change', {}).get(message.control, 'Unknown Knob/Fader')
#         return f"{timestamp:.3f} seconds: Knob/Fader ({control_name}) turned, value {message.value}"
    
#     elif message.type == 'pitchwheel':
#         return f"{timestamp:.3f} seconds: Jog Wheel rotated, value {message.pitch}"

#     else:
#         return f"{timestamp:.3f} seconds: Unknown MIDI message {message}"

# Function to log MIDI messages to a file
def log_midi_message(message, timestamp, log_file):
    log_entry = f"{timestamp:.3f} seconds: {message}\n"  # Log with millisecond precisionformat_midi_message(message, timestamp)
    with open(log_file, 'a') as f:
        f.write(log_entry + '\n')
    print(log_entry)

# Function to handle MIDI recording
def record_midi(log_file):
    global is_recording
    start_time = time.time()
    midi_input_port = mido.get_input_names()[0]
    
    try:
        with mido.open_input(midi_input_port) as inport:
            while is_recording:
                for message in inport.iter_pending():
                    timestamp = time.time() - start_time
                    log_midi_message(message, timestamp, log_file)
                time.sleep(0.01)  # Short sleep to prevent busy-waiting

    except Exception as e:
        print(f"Error: {e}")

# Function to record audio
def record_audio():
    global is_recording, audio_filename
    with sf.SoundFile(audio_filename, mode='w', samplerate=44100, channels=2) as audio_file:
        with sd.InputStream(samplerate=44100, channels=2, device=0) as audio_stream:
            while is_recording:
                audio_data, _ = audio_stream.read(1024)
                audio_file.write(audio_data)
                time.sleep(0.01)  # Short sleep to prevent busy-waiting

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
            midi_thread = threading.Thread(target=record_midi, args=(log_file_path,))
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
    app = QApplication([])
    window = MidiRecorderApp()
    window.show()
    app.exec_()
