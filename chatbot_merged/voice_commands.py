import asyncio
import pipeline
import whisper
import subprocess
import speech_recognition as sr   # Can be used for handling mic input thru the browser


# Load Whisper **once** at import
# Avoids reloading model everytime you call "listen_for_commands()"
whisper_model = whisper.load_model("base")

async def listen_for_commands(file_path: str):
    """
    Transcribe uploaded audio file using Whisper,
    then pass transcription into the pipeline processor
     
    Args:
        file_path (str): Path to the audio file (.wav, .mp3, etc.)

    Returns:
        str: The transcription text
    """

    # Run transcription
    result = whisper_model.transcribe(file_path)
    text = result["text"]

    # Send transcription into your custom processing pipeline
    processor = pipeline.Processor()
    await processor.process_command(text)
    return text

def run_hazard_detection():
    """
    Run hazard detection subprocess
    Run 'hazard_detection.py' w/ YOLO model argument
    """

    subprocess.run(["python", "hazard_detection.py", "--model", "yolov8n.pt"])

# Standalone script entry point

if __name__ == "__main__":
    # This will throw an error w/o an argument
    # Consider adding CLI parsing or a default file path
    asyncio.run(listen_for_commands())
