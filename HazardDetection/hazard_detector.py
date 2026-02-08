# hazard_detector.py
import os
import sys
import json
import time
import zipfile
import argparse
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

import cv2
import numpy as np
from PIL import Image

from google import genai
from google.genai import types
from twilio.rest import Client
from difflib import SequenceMatcher

load_dotenv()  # loads .env in current dir

# SMS Configuration
SMS_ENABLED = True  # Set to False to disable SMS notifications
SMS_TO_NUMBER = "+13657780651"  # Target phone number


class HazardMemory:
    """
    Track notified hazards to prevent duplicate SMS notifications.
    Uses fuzzy string matching on hazard type + location.
    """
    
    def __init__(self, cooldown_seconds: float = 3600.0, similarity_threshold: float = 0.75):
        """
        Initialize hazard memory.
        
        Args:
            cooldown_seconds: Time in seconds before a similar hazard can be notified again (default: 1 hour)
            similarity_threshold: Minimum similarity ratio (0-1) to consider hazards as duplicates (default: 0.75)
        """
        self._memory: dict[str, float] = {}  # signature -> timestamp
        self._cooldown = cooldown_seconds
        self._threshold = similarity_threshold
    
    def _normalize(self, s: str) -> str:
        """Normalize string to lowercase and strip whitespace."""
        return s.lower().strip() if s else ""
    
    def _make_signature(self, hazard: dict) -> str:
        """Create signature from normalized hazard type and location."""
        hazard_type = self._normalize(hazard.get("type", ""))
        location = self._normalize(hazard.get("location", ""))
        return f"{hazard_type}|{location}"
    
    def _find_similar(self, signature: str) -> str | None:
        """
        Find existing signature with >= similarity_threshold match.
        
        Returns:
            The existing signature if found, None otherwise.
        """
        for existing_sig in self._memory:
            ratio = SequenceMatcher(None, signature, existing_sig).ratio()
            if ratio >= self._threshold:
                return existing_sig
        return None
    
    def should_notify(self, hazard: dict) -> bool:
        """
        Check if a hazard should trigger a notification.
        
        Returns:
            True if hazard is new or cooldown has expired, False if duplicate within cooldown.
        """
        signature = self._make_signature(hazard)
        similar_sig = self._find_similar(signature)
        
        if similar_sig is None:
            # New hazard, never seen before
            return True
        
        # Check if cooldown has expired
        last_notified = self._memory.get(similar_sig, 0)
        elapsed = time.time() - last_notified
        return elapsed >= self._cooldown
    
    def record_notification(self, hazard: dict) -> None:
        """Record that a notification was sent for this hazard."""
        signature = self._make_signature(hazard)
        similar_sig = self._find_similar(signature)
        
        # Use existing similar signature if found, otherwise use new signature
        key = similar_sig if similar_sig else signature
        self._memory[key] = time.time()


# Global hazard memory for deduplication
hazard_memory = HazardMemory(cooldown_seconds=3600.0)  # 1 hour cooldown


HAZARD_PROMPT = """You are a safety inspector.

Analyze the image and detect if there are any hazards that could pose a risk to people navigating the space, especially in hallways and walkways.

Respond ONLY in this JSON shape:

{
  "hazard_detected": true/false,
  "hazard_detected_confidence": 0-100 (confidence score as percentage for hazard_detected, where 100 is highest confidence),
  "hazards": [
    {
      "type": "identification of the hazard (e.g. wet floor, exposed wires, pointed furniture edges, sharp table corners, bed corners, etc.)",
      "location": "specific location respective to the room/fixed objects, not respective to the person. Do not mention the person in the location (e.g. left side of door, second last step, corner of table, edge of bed)",
      "severity": "low/medium/high" (consider both how dangerous the hazard is and its position in the navigation path. Sharp edges and pointed corners in walkways should be flagged as hazards),
      "confidence": 0-100 (confidence score as percentage for this specific hazard detection, where 100 is highest confidence),
      "details": "extra context if useful",
      "sms_text": "ultra-concise SMS alert text in format: 'hazard near location' (max 50 chars, e.g. 'wet floor near hallway entrance', 'sharp table edge near wall')"
    }
  ],
  "people_detected": true/false,
  "people_detected_confidence": 0-100 (confidence score as percentage for people_detected, where 100 is highest confidence),
  "summary": "short 1-2 sentence summary"
}

Rules:
- If you see no hazards, set "hazard_detected": false and "hazards": [].
- Focus on immediate physical/safety hazards only.
- IMPORTANT: Detect furniture with pointed edges, sharp corners, or protruding edges (tables, beds, cabinets, etc.) as hazards, especially if they are positioned in or near walkways, hallways, or navigation paths.
- Detect hazards even when no people are visible in the image - the goal is to identify potential risks in the environment.
- Do NOT wrap the JSON in markdown.
- sms_text must be very short (max 50 chars) and describe the hazard and location concisely.
- REQUIRED: Include confidence scores (0-100 as percentages) for hazard_detected, people_detected, and each individual hazard. Higher values indicate higher confidence in the detection.
"""

def detect_hazards(image_input: str | np.ndarray, api_key: str | None = None) -> dict:
    """
    Run Gemini on an image and return hazard JSON.
    Uses the new google-genai SDK with gemini-2.5-flash-lite (15 RPM on free tier).
    
    Args:
        image_input: Either a file path (str) or a numpy array (video frame)
        api_key: Optional API key (otherwise reads from GEMINI_API_KEY env var)
    """
    # 1) API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in .env or pass api_key to detect_hazards().")

    # 2) Get image bytes - handle both file path and numpy array
    if isinstance(image_input, str):
        # File path
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image not found: {image_input}")
        with open(image_input, "rb") as f:
            image_bytes = f.read()
        mime_type = _guess_mime(image_input)
    elif isinstance(image_input, np.ndarray):
        # Numpy array (video frame)
        # Convert BGR (OpenCV) to RGB
        frame_rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        # Convert to bytes
        byte_io = BytesIO()
        pil_image.save(byte_io, format='JPEG')
        image_bytes = byte_io.getvalue()
        mime_type = "image/jpeg"
    else:
        raise ValueError("image_input must be either a file path (str) or numpy array")

    # 3) create client (Gemini Developer API)
    client = genai.Client(api_key=api_key)

    # 4) call model
    # using gemini-2.5-flash-lite for cost-effective responses (15 RPM)
    resp = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[
            # image first
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            ),
            # then instruction
            HAZARD_PROMPT,
        ],
        # tell it we want text back
        config=types.GenerateContentConfig(
            response_modalities=["TEXT"],
            # optional: push it to stick to JSON
            # but we'll still json.loads with a fallback
            temperature=0.2,
        ),
    )

    text = resp.text.strip()

    # 6) try to parse JSON
    # model might still wrap in ```json ... ``` so strip that
    text = _strip_md_fences(text)

    try:
        data = json.loads(text)
        return data
    except json.JSONDecodeError:
        # return raw for debugging
        return {
            "parsed": False,
            "raw_response": text,
        }


def _guess_mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    # fallback
    return "image/png"


def _strip_md_fences(s: str) -> str:
    # handles ```json ... ``` or ``` ... ```
    if s.startswith("```"):
        # remove first fence
        s = s.lstrip("`")
        # after removing leading ```json or ``` we may still have \n
        s = s.split("\n", 1)[1] if "\n" in s else s
        # remove trailing ```
        if "```" in s:
            s = s.rsplit("```", 1)[0]
        s = s.strip()
    return s


def send_sms_alert(hazard_data: dict, frame_number: int = None, timestamp: float = None) -> bool:
    """
    Send one SMS alert per hazard detected.
    
    Args:
        hazard_data: The hazard detection result dictionary
        frame_number: Optional frame number (for video mode)
        timestamp: Optional video timestamp (for video mode)
    
    Returns:
        True if all SMS sent successfully, False otherwise
    """
    if not SMS_ENABLED:
        return False
    
    # Check if hazard is actually detected
    if not hazard_data.get("hazard_detected", False):
        return False
    
    # Get Twilio credentials from environment
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, from_number]):
        print("⚠️  SMS Alert disabled: Missing Twilio credentials in .env file")
        return False
    
    hazards = hazard_data.get("hazards", [])
    if not hazards:
        return False
    
    all_sent = True
    client = Client(account_sid, auth_token)
    
    # Send one SMS per hazard
    for hazard in hazards:
        # Check for duplicate hazard (deduplication)
        if not hazard_memory.should_notify(hazard):
            print(f"⏭️ Skipping duplicate hazard: {hazard.get('type')} at {hazard.get('location')}")
            continue
        
        try:
            # Use AI-generated SMS text if available, otherwise fallback
            sms_text = hazard.get('sms_text')
            if not sms_text:
                # Fallback: create from type and location
                hazard_type = hazard.get('type', 'Unknown hazard')
                location = hazard.get('location', 'unknown location')
                sms_text = f"{hazard_type} near {location}"[:50]
            
            # Build message: "HAZARD: {sms_text}"
            message = f"HAZARD: {sms_text}"
            
            # Send SMS via Twilio
            sms = client.messages.create(
                body=message,
                from_=from_number,
                to=SMS_TO_NUMBER
            )
            
            print(f"SMS sent: '{message}' (SID: {sms.sid})")
            
            # Record successful notification for deduplication
            hazard_memory.record_notification(hazard)
            
        except Exception as e:
            print(f"Failed to send SMS: {e}")
            all_sent = False
    
    return all_sent


def process_video_continuous(video_path: str, poll_interval: float = 4.0, api_key: str | None = None) -> None:
    """
    Process a video file, extracting and analyzing frames every poll_interval seconds.
    Stops when the video ends.
    
    Args:
        video_path: Path to the video file
        poll_interval: Time in seconds between frame analyses (default: 4.0 for 15 RPM limit)
        api_key: Optional API key
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    print(f"Starting video monitoring: {video_path}")
    print(f"Polling interval: {poll_interval} seconds (respects 15 RPM rate limit)")
    print("Press Ctrl+C to stop\n")
    
    frame_count = 0
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        print(f"Video info: {fps:.2f} FPS, {total_frames} frames, {duration:.2f}s duration")
        print(f"Starting video analysis...\n")
        
        current_position = 0
        frames_to_skip = int(fps * poll_interval) if fps > 0 else 1
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                # End of video
                print("\nReached end of video.")
                break
            
            # Process frame at poll_interval
            if current_position % frames_to_skip == 0:
                frame_count += 1
                timestamp = current_position / fps if fps > 0 else 0
                
                print(f"[Frame {frame_count}] Video timestamp: {timestamp:.2f}s")
                print(f"Analyzing frame at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
                
                try:
                    result = detect_hazards(frame, api_key=api_key)
                    print_results(result)
                    
                    # Send SMS alert if hazard detected
                    if result.get("hazard_detected", False):
                        send_sms_alert(result, frame_number=frame_count, timestamp=timestamp)
                except Exception as e:
                    print(f"Error analyzing frame: {e}")
                
                # Wait for next poll interval (already spent time on API call)
                time.sleep(poll_interval)
            
            current_position += 1
        
        cap.release()
        print(f"\nVideo analysis complete. Total frames analyzed: {frame_count}")
            
    except KeyboardInterrupt:
        print("\n\nStopping video monitoring...")
        print(f"Total frames analyzed: {frame_count}")
    except Exception as e:
        print(f"\nError during video processing: {e}")
        sys.exit(1)


def process_zip_images(zip_path: str, output_file: str = "testing_documentation/hallway_images.txt", 
                       api_key: str | None = None, poll_interval: float = 4.0) -> list:
    """
    Process all JPG images from a zip file and document results in a text file.
    
    Args:
        zip_path: Path to the zip file containing JPG images
        output_file: Path to the output text file for documenting results
        api_key: Optional API key (otherwise reads from GEMINI_API_KEY env var)
        poll_interval: Time in seconds between image analyses (default: 4.0 for 15 RPM limit)
    """
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Zip file not found: {zip_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Get API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in .env or pass api_key to process_zip_images().")
    
    print(f"Processing zip file: {zip_path}")
    print(f"Results will be written to: {output_file}")
    print(f"Polling interval: {poll_interval} seconds (respects 15 RPM rate limit)\n")
    
    # Extract JPG images from zip
    image_files = []
    temp_extract_dir = None
    image_results = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of JPG files
            for file_info in zip_ref.namelist():
                if file_info.lower().endswith(('.jpg', '.jpeg')):
                    image_files.append(file_info)
        
        if not image_files:
            print("No JPG/JPEG files found in the zip archive.")
            return
        
        print(f"Found {len(image_files)} JPG image(s) in zip file.\n")
        
        # Create temporary directory for extraction
        temp_extract_dir = os.path.join(os.path.dirname(zip_path), f"temp_extract_{int(time.time())}")
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        # Extract images
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for image_file in image_files:
                zip_ref.extract(image_file, temp_extract_dir)
        
        # Open output file for writing
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("HALLWAY IMAGE HAZARD DETECTION TEST RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source Zip: {os.path.basename(zip_path)}\n")
            f.write(f"Total Images: {len(image_files)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Process each image
            for idx, image_file in enumerate(image_files, 1):
                image_path = os.path.join(temp_extract_dir, image_file)
                
                print(f"[{idx}/{len(image_files)}] Processing: {image_file}")
                print(f"Analyzing image at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
                
                try:
                    # Analyze image
                    result = detect_hazards(image_path, api_key=api_key)
                    
                    # Store image result with path
                    image_result = {
                        "image_path": image_path,
                        "image_filename": image_file,
                        "result": result
                    }
                    image_results.append(image_result)
                    
                    # Write results to file
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"IMAGE #{idx}: {image_file}\n")
                    f.write(f"{'=' * 80}\n")
                    f.write(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    if result.get("parsed") is False:
                        f.write("ERROR: Could not parse JSON response from AI model.\n")
                        f.write(f"Raw Response:\n{result.get('raw_response', 'N/A')}\n\n")
                    else:
                        people = result.get("people_detected", False)
                        hazard = result.get("hazard_detected", False)
                        hazards = result.get("hazards", [])
                        summary = result.get("summary", "N/A")
                        people_confidence = result.get("people_detected_confidence")
                        hazard_confidence = result.get("hazard_detected_confidence")
                        
                        f.write(f"People Detected: {'Yes' if people else 'No'}\n")
                        people_conf_str = _format_confidence(people_confidence)
                        if people_conf_str:
                            f.write(f"  Confidence: {people_conf_str}\n")
                        f.write(f"Hazard Detected: {'Yes' if hazard else 'No'}\n")
                        hazard_conf_str = _format_confidence(hazard_confidence)
                        if hazard_conf_str:
                            f.write(f"  Confidence: {hazard_conf_str}\n")
                        f.write(f"Summary: {summary}\n\n")
                        
                        if hazards:
                            f.write(f"Hazards Found: {len(hazards)}\n")
                            for i, h in enumerate(hazards, 1):
                                f.write(f"\n  Hazard #{i}:\n")
                                f.write(f"    Type: {h.get('type', 'N/A')}\n")
                                f.write(f"    Location: {h.get('location', 'N/A')}\n")
                                f.write(f"    Severity: {h.get('severity', 'N/A')}\n")
                                conf_str = _format_confidence(h.get('confidence'))
                                if conf_str:
                                    f.write(f"    Confidence: {conf_str}\n")
                                f.write(f"    Details: {h.get('details', 'N/A')}\n")
                                f.write(f"    SMS Text: {h.get('sms_text', 'N/A')}\n")
                            
                            # Classify overall hazard severity
                            severity_level, severity_percentage = classify_hazard_severity(len(hazards))
                            f.write(f"\nOverall Hazard Severity: {severity_level} ({severity_percentage}%)\n")
                        else:
                            f.write("Hazards Found: 0\n")
                            f.write("Status: No obstacles or hazards detected.\n")
                            # Classify severity for no hazards case
                            severity_level, severity_percentage = classify_hazard_severity(0)
                            f.write(f"Overall Hazard Severity: {severity_level} ({severity_percentage}%)\n")
                    
                    f.write("\n")
                    
                    # Also print to console
                    print_results(result)
                    
                    # Wait before next image (except for last one)
                    if idx < len(image_files):
                        print(f"\nWaiting {poll_interval} seconds before next image...\n")
                        time.sleep(poll_interval)
                
                except Exception as e:
                    error_msg = f"Error analyzing {image_file}: {e}"
                    print(f"ERROR: {error_msg}")
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"IMAGE #{idx}: {image_file}\n")
                    f.write(f"{'=' * 80}\n")
                    f.write(f"ERROR: {error_msg}\n\n")
                    
                    # Store error result
                    image_result = {
                        "image_path": image_path,
                        "image_filename": image_file,
                        "error": error_msg
                    }
                    image_results.append(image_result)
            
            # Write footer
            f.write("\n" + "=" * 80 + "\n")
            f.write("END OF TEST RESULTS\n")
            f.write("=" * 80 + "\n")
        
        print(f"\n{'=' * 60}")
        print(f"Batch processing complete!")
        print(f"Results documented in: {output_file}")
        print(f"Total images processed: {len(image_files)}")
        print(f"{'=' * 60}")
    
    finally:
        # Clean up temporary extraction directory
        if temp_extract_dir and os.path.exists(temp_extract_dir):
            import shutil
            shutil.rmtree(temp_extract_dir)
            print(f"\nCleaned up temporary files.")
    
    return image_results


def process_directory_images(image_dir: str, output_file: str = "testing_documentation/hallway_images.txt", 
                             api_key: str | None = None, poll_interval: float = 4.0) -> list:
    """
    Process all JPG images from a directory and document results in a text file.
    
    Args:
        image_dir: Path to the directory containing JPG images
        output_file: Path to the output text file for documenting results
        api_key: Optional API key (otherwise reads from GEMINI_API_KEY env var)
        poll_interval: Time in seconds between image analyses (default: 4.0 for 15 RPM limit)
    """
    if not os.path.exists(image_dir):
        raise FileNotFoundError(f"Directory not found: {image_dir}")
    
    if not os.path.isdir(image_dir):
        raise ValueError(f"Path is not a directory: {image_dir}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Get API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in .env or pass api_key to process_directory_images().")
    
    print(f"Processing directory: {image_dir}")
    print(f"Results will be written to: {output_file}")
    print(f"Polling interval: {poll_interval} seconds (respects 15 RPM rate limit)\n")
    
    # Get list of JPG files from directory
    image_results = []
    image_files = []
    for file in os.listdir(image_dir):
        if file.lower().endswith(('.jpg', '.jpeg')):
            image_files.append(file)
    
    # Sort for consistent ordering
    image_files.sort()
    
    if not image_files:
        print("No JPG/JPEG files found in the directory.")
        return
    
    print(f"Found {len(image_files)} JPG image(s) in directory.\n")
    
    # Open output file for writing
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("=" * 80 + "\n")
        f.write("HAZARD DETECTION TEST RESULTS - BATCH TESTING\n")
        f.write("=" * 80 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Directory: {image_dir}\n")
        f.write(f"Total Images: {len(image_files)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Process each image
        for idx, image_file in enumerate(image_files, 1):
            image_path = os.path.join(image_dir, image_file)
            
            print(f"[{idx}/{len(image_files)}] Processing: {image_file}")
            print(f"Analyzing image at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
            
            try:
                # Analyze image
                result = detect_hazards(image_path, api_key=api_key)
                
                # Store image result with path
                image_result = {
                    "image_path": image_path,
                    "image_filename": image_file,
                    "result": result
                }
                image_results.append(image_result)
                
                # Write results to file
                f.write(f"\n{'=' * 80}\n")
                f.write(f"IMAGE #{idx}: {image_file}\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if result.get("parsed") is False:
                    f.write("ERROR: Could not parse JSON response from AI model.\n")
                    f.write(f"Raw Response:\n{result.get('raw_response', 'N/A')}\n\n")
                else:
                    people = result.get("people_detected", False)
                    hazard = result.get("hazard_detected", False)
                    hazards = result.get("hazards", [])
                    summary = result.get("summary", "N/A")
                    people_confidence = result.get("people_detected_confidence")
                    hazard_confidence = result.get("hazard_detected_confidence")
                    
                    f.write(f"People Detected: {'Yes' if people else 'No'}\n")
                    people_conf_str = _format_confidence(people_confidence)
                    if people_conf_str:
                        f.write(f"  Confidence: {people_conf_str}\n")
                    f.write(f"Hazard Detected: {'Yes' if hazard else 'No'}\n")
                    hazard_conf_str = _format_confidence(hazard_confidence)
                    if hazard_conf_str:
                        f.write(f"  Confidence: {hazard_conf_str}\n")
                    f.write(f"Summary: {summary}\n\n")
                    
                    if hazards:
                        f.write(f"Hazards Found: {len(hazards)}\n")
                        for i, h in enumerate(hazards, 1):
                            f.write(f"\n  Hazard #{i}:\n")
                            f.write(f"    Type: {h.get('type', 'N/A')}\n")
                            f.write(f"    Location: {h.get('location', 'N/A')}\n")
                            f.write(f"    Severity: {h.get('severity', 'N/A')}\n")
                            conf_str = _format_confidence(h.get('confidence'))
                            if conf_str:
                                f.write(f"    Confidence: {conf_str}\n")
                            f.write(f"    Details: {h.get('details', 'N/A')}\n")
                            f.write(f"    SMS Text: {h.get('sms_text', 'N/A')}\n")
                        
                        # Classify overall hazard severity
                        severity_level, severity_percentage = classify_hazard_severity(len(hazards))
                        f.write(f"\nOverall Hazard Severity: {severity_level} ({severity_percentage}%)\n")
                    else:
                        f.write("Hazards Found: 0\n")
                        f.write("Status: No obstacles or hazards detected.\n")
                        # Classify severity for no hazards case
                        severity_level, severity_percentage = classify_hazard_severity(0)
                        f.write(f"Overall Hazard Severity: {severity_level} ({severity_percentage}%)\n")
                
                f.write("\n")
                
                # Also print to console
                print_results(result)
                
                # Wait before next image (except for last one)
                if idx < len(image_files):
                    print(f"\nWaiting {poll_interval} seconds before next image...\n")
                    time.sleep(poll_interval)
            
            except Exception as e:
                error_msg = f"Error analyzing {image_file}: {e}"
                print(f"ERROR: {error_msg}")
                f.write(f"\n{'=' * 80}\n")
                f.write(f"IMAGE #{idx}: {image_file}\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"ERROR: {error_msg}\n\n")
                
                # Store error result
                image_result = {
                    "image_path": image_path,
                    "image_filename": image_file,
                    "error": error_msg
                }
                image_results.append(image_result)
        
        # Write footer
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF TEST RESULTS\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n{'=' * 60}")
    print(f"Batch processing complete!")
    print(f"Results documented in: {output_file}")
    print(f"Total images processed: {len(image_files)}")
    print(f"{'=' * 60}")
    
    return image_results


def _format_confidence(confidence) -> str | None:
    """
    Convert confidence score to percentage format.
    Handles both decimal (0.0-1.0) and percentage (0-100) formats.
    
    Args:
        confidence: Confidence score as float/int (0.0-1.0 or 0-100)
    
    Returns:
        Formatted string as percentage (e.g., "85%") or None if confidence is None
    """
    if confidence is None:
        return None
    
    try:
        conf_value = float(confidence)
        # If value is <= 1.0, assume it's decimal format and convert to percentage
        if conf_value <= 1.0:
            conf_value = conf_value * 100
        # Ensure it's within 0-100 range
        conf_value = max(0, min(100, conf_value))
        return f"{conf_value:.0f}%"
    except (ValueError, TypeError):
        return None


def classify_hazard_severity(num_hazards, area_coverage=None):
    """
    Classify hazard severity based on number of hazards and optional parameters.
    
    Parameters:
    - num_hazards: Number of hazards detected (int)
    - area_coverage: Optional, percentage of area covered by hazards (0-100)
    
    Returns:
    - severity_level: String ('Safe', 'Low', 'Medium', 'High', 'Critical')
    - severity_percentage: Float (0-100)
    """
    
    # Base severity on number of hazards
    if num_hazards == 0:
        base_severity = 0
    elif num_hazards == 1:
        base_severity = 10
    elif num_hazards == 2:
        base_severity = 20
    elif num_hazards == 3:
        base_severity = 30
    elif num_hazards == 4:
        base_severity = 40
    elif num_hazards == 5:
        base_severity = 50
    elif num_hazards == 6:
        base_severity = 60
    elif num_hazards == 7:
        base_severity = 70
    elif num_hazards == 8:
        base_severity = 80
    elif num_hazards <= 10:
        base_severity = 90
    else:
        base_severity = 100
    
    # Adjust for area coverage if provided
    if area_coverage is not None:
        coverage_factor = area_coverage / 100
        base_severity = min(100, base_severity + (coverage_factor * 20))
    
    # Classify severity level
    if base_severity == 0:
        severity_level = "Safe"
    elif base_severity < 40:
        severity_level = "Low"
    elif base_severity < 60:
        severity_level = "Medium"
    elif base_severity < 80:
        severity_level = "High"
    else:
        severity_level = "Critical"
    
    return severity_level, round(base_severity, 2)


def print_results(result: dict) -> None:
    print("\n" + "=" * 60)
    print("HAZARD DETECTION RESULTS")
    print("=" * 60)

    if result.get("parsed") is False:
        print("\nCould not parse JSON. Raw model output:\n")
        print(result.get("raw_response"))
        print("\n" + "=" * 60)
        return

    people = result.get("people_detected", False)
    hazard = result.get("hazard_detected", False)
    hazards = result.get("hazards", [])
    people_confidence = result.get("people_detected_confidence")
    hazard_confidence = result.get("hazard_detected_confidence")

    print(f"\nPeople Detected: {'Yes' if people else 'No'}")
    people_conf_str = _format_confidence(people_confidence)
    if people_conf_str:
        print(f"  Confidence: {people_conf_str}")
    print(f"Hazard Detected: {'Yes' if hazard else 'No'}")
    hazard_conf_str = _format_confidence(hazard_confidence)
    if hazard_conf_str:
        print(f"  Confidence: {hazard_conf_str}")

    if hazards:
        print(f"\nNumber of Hazards: {len(hazards)}")
        for i, h in enumerate(hazards, 1):
            print(f"\n  Hazard #{i}:")
            print(f"    Type: {h.get('type', 'N/A')}")
            print(f"    Location: {h.get('location', 'N/A')}")
            print(f"    Severity: {h.get('severity', 'N/A')}")
            conf_str = _format_confidence(h.get('confidence'))
            if conf_str:
                print(f"    Confidence: {conf_str}")
            print(f"    Details: {h.get('details', 'N/A')}")
        
        # Classify overall hazard severity
        severity_level, severity_percentage = classify_hazard_severity(len(hazards))
        print(f"\nOverall Hazard Severity: {severity_level} ({severity_percentage}%)")
    else:
        print("\nNo hazards listed.")
        # Classify severity for no hazards case
        severity_level, severity_percentage = classify_hazard_severity(0)
        print(f"Overall Hazard Severity: {severity_level} ({severity_percentage}%)")

    summary = result.get("summary")
    if summary:
        print(f"\nSummary: {summary}")

    print("\n" + "=" * 60)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Hazard Detection using Gemini AI')
    parser.add_argument('--mode', type=str, choices=['image', 'video', 'batch', 'directory'],
                       default='directory', help='Mode: image, video, batch, or directory')
    parser.add_argument('--image-filename', type=str, default='image.png',
                       help='Image filename for image mode')
    parser.add_argument('--video-filename', type=str, default='messyPath.mp4',
                       help='Video filename for video mode')
    parser.add_argument('--zip-filename', type=str, default='hallway_images.zip',
                       help='Zip filename for batch mode')
    parser.add_argument('--image-dir', type=str, default='test_images',
                       help='Image directory for directory mode')
    parser.add_argument('--output-file', type=str, default='testing_documentation/hallway_images.txt',
                       help='Output file path for batch and directory modes')
    parser.add_argument('--poll-interval', type=float, default=4.0,
                       help='Poll interval in seconds for video/batch/directory modes')
    
    args = parser.parse_args()
    
    MODE = args.mode
    IMAGE_FILENAME = args.image_filename
    VIDEO_FILENAME = args.video_filename
    ZIP_FILENAME = args.zip_filename
    IMAGE_DIR = args.image_dir
    OUTPUT_FILE = args.output_file
    POLL_INTERVAL = args.poll_interval
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if MODE == "image":
        image_path = os.path.join(script_dir, IMAGE_FILENAME)
        print(f"Mode: Single Image Analysis")
        print(f"Looking for image: {image_path}\n")
        
        try:
            result = detect_hazards(image_path)
            print_results(result)
            
            # Send SMS alert if hazard detected
            if result.get("hazard_detected", False):
                send_sms_alert(result)
            
            # Output JSON results for frontend
            json_result = {
                "mode": "image",
                "images": [{
                    "image_path": image_path,
                    "image_filename": IMAGE_FILENAME,
                    "result": result
                }]
            }
            print("\nJSON_RESULTS_START:")
            print(json.dumps(json_result))
            print("JSON_RESULTS_END")
        except Exception as e:
            print(f"Error: {e}")
            json_result = {
                "mode": "image",
                "images": [{
                    "image_path": image_path,
                    "image_filename": IMAGE_FILENAME,
                    "error": str(e)
                }]
            }
            print("\nJSON_RESULTS_START:")
            print(json.dumps(json_result))
            print("JSON_RESULTS_END")
            sys.exit(1)
    
    elif MODE == "video":
        # Continuous video monitoring
        video_path = os.path.join(script_dir, VIDEO_FILENAME)
        print(f"Mode: Continuous Video Monitoring")
        print(f"Looking for video: {video_path}\n")
        
        try:
            process_video_continuous(video_path, poll_interval=POLL_INTERVAL)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif MODE == "batch":
        # Batch processing from zip file
        zip_path = os.path.join(script_dir, ZIP_FILENAME)
        # Handle both relative and absolute paths for output file
        if os.path.isabs(OUTPUT_FILE):
            output_path = OUTPUT_FILE
        else:
            output_path = os.path.join(script_dir, OUTPUT_FILE)
        print(f"Mode: Batch Image Processing from Zip")
        print(f"Looking for zip file: {zip_path}\n")
        
        try:
            image_results = process_zip_images(zip_path, output_file=output_path, poll_interval=POLL_INTERVAL)
            
            # Output JSON results for frontend
            json_result = {
                "mode": "batch",
                "images": image_results
            }
            print("\nJSON_RESULTS_START:")
            print(json.dumps(json_result))
            print("JSON_RESULTS_END")
        except Exception as e:
            print(f"Error: {e}")
            json_result = {
                "mode": "batch",
                "images": [],
                "error": str(e)
            }
            print("\nJSON_RESULTS_START:")
            print(json.dumps(json_result))
            print("JSON_RESULTS_END")
            sys.exit(1)
    
    elif MODE == "directory":
        # Batch processing from directory
        # Handle both relative and absolute paths
        if os.path.isabs(IMAGE_DIR):
            image_dir_path = IMAGE_DIR
        else:
            image_dir_path = os.path.join(script_dir, IMAGE_DIR)
        
        # Handle both relative and absolute paths for output file
        if os.path.isabs(OUTPUT_FILE):
            output_path = OUTPUT_FILE
        else:
            output_path = os.path.join(script_dir, OUTPUT_FILE)
        
        print(f"Mode: Batch Image Processing from Directory")
        print(f"Looking for directory: {image_dir_path}\n")
        
        try:
            image_results = process_directory_images(image_dir_path, output_file=output_path, poll_interval=POLL_INTERVAL)
            
            # Output JSON results for frontend
            json_result = {
                "mode": "directory",
                "images": image_results
            }
            print("\nJSON_RESULTS_START:")
            print(json.dumps(json_result))
            print("JSON_RESULTS_END")
        except Exception as e:
            print(f"Error: {e}")
            json_result = {
                "mode": "directory",
                "images": [],
                "error": str(e)
            }
            print("\nJSON_RESULTS_START:")
            print(json.dumps(json_result))
            print("JSON_RESULTS_END")
            sys.exit(1)
    
    else:
        print(f"Error: Invalid MODE '{MODE}'. Must be 'image', 'video', 'batch', or 'directory'")
        sys.exit(1)


if __name__ == "__main__":
    main()