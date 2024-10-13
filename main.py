import mido
import time
import os

# Function to log MIDI messages to a file
def log_midi_message(message, timestamp, log_file):
    with open(log_file, 'a') as f:
        log_entry = f"{timestamp:.3f} seconds: {message}\n"  # Log with millisecond precision
        f.write(log_entry)
        print(log_entry)  # Optional: Print to console for real-time feedback

def main(log_file='midi_log.txt'):
    # Get the start time (in seconds)
    start_time = time.time()

    # Open a MIDI input port
    try:
        print("Available MIDI input ports:")
        for i, port in enumerate(mido.get_input_names()):
            print(f"{i}: {port}")
        
        # Choose the first available MIDI port (you can change this to choose specific one)
        midi_input_port = mido.get_input_names()[0]
        print(f"Opening MIDI input: {midi_input_port}")
        with mido.open_input(midi_input_port) as inport:
            print("Listening for MIDI messages... (Press Ctrl+C to stop)")
            
            # Main loop to listen for incoming MIDI messages
            while True:
                for message in inport.iter_pending():
                    current_time = time.time()
                    timestamp = current_time - start_time  # Calculate time difference from start
                    log_midi_message(message, timestamp, log_file)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Specify the path for the log file
    log_file_path = os.path.join(os.getcwd(), 'midi_log.txt')
    main(log_file_path)
