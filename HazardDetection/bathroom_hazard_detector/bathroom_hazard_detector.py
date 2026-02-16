import os
import sys
import json
import time
import zipfile
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

import cv2
import numpy as np
from PIL import Image

from google import genai
from google.genai import types

load_dotenv()

# Supported Extensions for Directory/Zip Scanning
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.heic', '.heif')

# MIME types natively supported by Gemini API (others will be converted to JPEG)
NATIVE_GEMINI_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]

HAZARD_PROMPT = """You are an AI Home Safety Assessor. You will be provided with an image or a sequence of video frames from a senior's bathroom.

Your task is to conduct a "Falls Risk Assessment" based on the Westmead Home Safety Assessment (WeHSA) principles.

Analyze the visual input for the following specific safety categories:

1.  **Flooring & Walkways:**
    * Check for loose "throw rugs" or mats without rubber backing (High Trip Risk).
    * Check for clutter or obstacles on the floor.
    * Check for wet surfaces or lack of non-slip mats in the tub/shower.

2.  **Toilet Area:**
    * Check for the presence of dedicated, wall-mounted Grab Bars (Note: Towel racks are NOT grab bars).
    * Assess if the toilet appears to be standard height or has a raised seat attachment.

3.  **Bathing Area (Shower/Tub):**
    * Check for Grab Bars inside and entering the shower.
    * Check for a shower chair or transfer bench.
    * Check for a high step-over threshold (standard tub vs. walk-in).

4.  **Lighting & Visibility:**
    * Assess if the room appears dimly lit or has shadows obscuring floor hazards.
    * Check for high contrast between critical zones (e.g., toilet seat vs. floor).

**RESPONSE FORMAT:**
Return a single JSON object with the following structure:

{
  "overall_safety_score": "Integer (1-10, where 10 is safest)",
  "summary": "One sentence summary of the bathroom's safety status.",
  "hazards": [
    {
      "category": "Flooring | Toilet | Shower | Lighting",
      "description": "Specific observation (e.g., Loose rug found near sink)",
      "severity": "CRITICAL | MODERATE | LOW",
      "confidence": 0.0 to 1.0
    }
  ],
  "recommendations": [
    "Actionable suggestion 1",
    "Actionable suggestion 2"
  ],
  "missing_info": [
    "List of things you cannot see clearly but need to check"
  ]
}
"""

def detect_hazards(image_input: str | np.ndarray, api_key: str | None = None) -> dict:
    # 1) API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in .env or pass api_key to detect_hazards().")

    # 2) Get image bytes - handle both file path and numpy array
    image_bytes = None
    mime_type = "image/jpeg" # Default fallback

    try:
        if isinstance(image_input, str):
            # File path
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image not found: {image_input}")
            
            guessed_mime = _guess_mime(image_input)
            
            # If native Gemini format, read directly
            if guessed_mime in NATIVE_GEMINI_MIME_TYPES:
                with open(image_input, "rb") as f:
                    image_bytes = f.read()
                mime_type = guessed_mime
            else:
                # Convert non-native formats (BMP, TIFF, etc.) to JPEG
                # print(f"Converting {guessed_mime} to JPEG for API compatibility...")
                with Image.open(image_input) as img:
                    img = img.convert('RGB')
                    byte_io = BytesIO()
                    img.save(byte_io, format='JPEG')
                    image_bytes = byte_io.getvalue()
                    mime_type = "image/jpeg"

        elif isinstance(image_input, np.ndarray):
            # Numpy array (video frame) -> Convert to JPEG bytes
            frame_rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            byte_io = BytesIO()
            pil_image.save(byte_io, format='JPEG')
            image_bytes = byte_io.getvalue()
            mime_type = "image/jpeg"
        else:
            raise ValueError("image_input must be either a file path (str) or numpy array")

    except Exception as e:
        return {
            "parsed": False,
            "raw_response": f"Error processing image bytes: {e}",
            "hazard_detected": False
        }

    # 3) create client (Gemini Developer API)
    client = genai.Client(api_key=api_key)

    # 4) call model
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                HAZARD_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
                temperature=0.2,
            ),
        )
        text = resp.text.strip()
    except Exception as e:
        return {
            "parsed": False,
            "raw_response": f"API Error: {str(e)}",
            "hazard_detected": False
        }

    # 6) try to parse JSON
    text = _strip_md_fences(text)

    try:
        data = json.loads(text)
        # 1. Polyfill 'hazard_detected' based on whether hazards exist
        if "hazards" in data and len(data["hazards"]) > 0:
            data["hazard_detected"] = True
        else:
            data["hazard_detected"] = False
            data["hazards"] = [] # Ensure list exists
            
        # 2. Ensure other keys exist to prevent KeyErrors later
        if "summary" not in data: data["summary"] = "No summary provided."
        if "recommendations" not in data: data["recommendations"] = []
        if "overall_safety_score" not in data: data["overall_safety_score"] = 0
        return data
    except json.JSONDecodeError:
        return {
            "parsed": False,
            "raw_response": text,
            "hazard_detected": False 
        }


def _guess_mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg", ".jpe"]: return "image/jpeg"
    if ext == ".png": return "image/png"
    if ext == ".webp": return "image/webp"
    if ext in [".heic", ".heif"]: return "image/heic"
    if ext in [".tif", ".tiff"]: return "image/tiff"
    if ext == ".bmp": return "image/bmp"
    return "image/png" # Fallback


def _strip_md_fences(s: str) -> str:
    # handles ```json ... ``` or ``` ... ```
    if s.startswith("```"):
        s = s.lstrip("`")
        s = s.split("\n", 1)[1] if "\n" in s else s
        if "```" in s:
            s = s.rsplit("```", 1)[0]
        s = s.strip()
    return s

def log_result_to_file(file_handle, result, identifier, timestamp_str):
    """Helper to write formatted results to a file handle."""
    file_handle.write(f"\n{'=' * 80}\n")
    file_handle.write(f"SOURCE: {identifier}\n")
    file_handle.write(f"{'=' * 80}\n")
    file_handle.write(f"Analysis Time: {timestamp_str}\n\n")
    
    if result.get("parsed") is False:
        file_handle.write("ERROR: Could not parse JSON response from AI model.\n")
        file_handle.write(f"Raw Response:\n{result.get('raw_response', 'N/A')}\n\n")
    else:
        score = result.get("overall_safety_score", "N/A")
        summary = result.get("summary", "N/A")
        hazards = result.get("hazards", [])
        recommendations = result.get("recommendations", [])
        
        file_handle.write(f"Safety Score: {score}/10\n")
        file_handle.write(f"Summary: {summary}\n")
        file_handle.write(f"Hazards Detected: {len(hazards)}\n\n")
        
        if hazards:
            file_handle.write("--- DETECTED HAZARDS ---\n")
            for i, h in enumerate(hazards, 1):
                file_handle.write(f"  #{i} [{h.get('severity', 'UNK')}] {h.get('category', 'General')}\n")
                file_handle.write(f"     Description: {h.get('description', 'N/A')}\n")
                file_handle.write(f"     Confidence:  {h.get('confidence', 'N/A')}\n")
                file_handle.write("\n")
        
        if recommendations:
            file_handle.write("--- RECOMMENDATIONS ---\n")
            for rec in recommendations:
                file_handle.write(f"  - {rec}\n")
                
    file_handle.write("\n")
    file_handle.flush()


def process_video_continuous(video_path: str, poll_interval: float = 4.0, api_key: str | None = None) -> None:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    print(f"Starting video monitoring: {video_path}")
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame_count = 0
        current_position = 0
        frames_to_skip = int(fps * poll_interval) if fps > 0 else 1
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            if current_position % frames_to_skip == 0:
                frame_count += 1
                timestamp = current_position / fps if fps > 0 else 0
                print(f"[Frame {frame_count}] Video timestamp: {timestamp:.2f}s")
                
                try:
                    result = detect_hazards(frame, api_key=api_key)
                    print_results(result)
                except Exception as e:
                    print(f"Error analyzing frame: {e}")
                
                time.sleep(poll_interval)
            
            current_position += 1
        
        cap.release()
            
    except KeyboardInterrupt:
        print("\nStopping video monitoring...")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


def process_zip_images(zip_path: str, output_file: str = "bathroom_hazard_testing_results/zip_results.txt", 
                       api_key: str | None = None, poll_interval: float = 4.0) -> None:
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Zip file not found: {zip_path}")
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing zip file: {zip_path}")
    print(f"Results will be written to: {output_file}")
    
    image_files = []
    temp_extract_dir = None
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.namelist():
                if file_info.lower().endswith(VALID_EXTENSIONS):
                    image_files.append(file_info)
        
        if not image_files:
            print("No supported image files found in the zip archive.")
            return
        
        temp_extract_dir = os.path.join(os.path.dirname(zip_path), f"temp_extract_{int(time.time())}")
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for image_file in image_files:
                zip_ref.extract(image_file, temp_extract_dir)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"BATCH TEST RESULTS (ZIP)\nTest Date: {datetime.now()}\nFile: {zip_path}\n\n")
            
            for idx, image_file in enumerate(image_files, 1):
                image_path = os.path.join(temp_extract_dir, image_file)
                print(f"[{idx}/{len(image_files)}] Processing: {image_file}")
                
                try:
                    result = detect_hazards(image_path, api_key=api_key)
                    log_result_to_file(f, result, image_file, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    print_results(result)
                    
                    if idx < len(image_files):
                        time.sleep(poll_interval)
                except Exception as e:
                    print(f"ERROR processing {image_file}: {e}")
    
    finally:
        if temp_extract_dir and os.path.exists(temp_extract_dir):
            import shutil
            shutil.rmtree(temp_extract_dir)


def process_directory_images(image_dir: str, output_file: str = "bathroom_hazard_testing_results/directory_results.txt", 
                             api_key: str | None = None, poll_interval: float = 4.0) -> None:
    if not os.path.exists(image_dir) or not os.path.isdir(image_dir):
        raise ValueError(f"Invalid directory: {image_dir}")
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing directory: {image_dir}")
    print(f"Results will be written to: {output_file}")
    
    image_files = []
    for file in os.listdir(image_dir):
        if file.lower().endswith(VALID_EXTENSIONS):
            image_files.append(file)
    
    image_files.sort()
    
    if not image_files:
        print("No supported image files found in the directory.")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"BATCH TEST RESULTS (DIRECTORY)\nTest Date: {datetime.now()}\nDir: {image_dir}\n\n")
        
        for idx, image_file in enumerate(image_files, 1):
            image_path = os.path.join(image_dir, image_file)
            print(f"[{idx}/{len(image_files)}] Processing: {image_file}")
            
            try:
                result = detect_hazards(image_path, api_key=api_key)
                log_result_to_file(f, result, image_file, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                print_results(result)
                
                if idx < len(image_files):
                    time.sleep(poll_interval)
            except Exception as e:
                print(f"ERROR processing {image_file}: {e}")
    
    print(f"\nResults documented in: {output_file}")


def print_results(result: dict) -> None:
    print("\n" + "=" * 60)
    if result.get("parsed") is False:
        print("RAW RESPONSE (Parse Error):")
        print(result.get("raw_response"))
    else:
        score = result.get("overall_safety_score", "N/A")
        print(f"Safety Score: {score}/10")
        print(f"Hazard Detected: {result.get('hazard_detected')}")
        
        hazards = result.get("hazards", [])
        if hazards:
            print(f"Hazards Found: {len(hazards)}")
            for h in hazards:
                cat = h.get('category', 'General')
                desc = h.get('description', 'No description')
                sev = h.get('severity', 'UNK')
                print(f"- [{sev}] {cat}: {desc}")
        else:
            print("Status: Safe (No hazards detected)")

        print(f"Summary: {result.get('summary')}")
    print("=" * 60)


def main():
    MODE = "directory"  # Options: "image", "video", "batch", "directory"
    
    # Configuration
    POLL_INTERVAL = 4.0
    
    # 1. Image Mode Config
    IMAGE_FILENAME = "image.bmp" # Can be any format now
    IMAGE_OUTPUT = "bathroom_hazard_testing_results/single_image_results.txt"
    
    # 2. Directory Mode Config
    IMAGE_DIR = "bathroom_test_images"
    DIR_OUTPUT = "bathroom_hazard_testing_results/directory_results.txt"
    
    # 3. Batch/Zip Mode Config
    ZIP_FILENAME = "hallway_images.zip"
    ZIP_OUTPUT = "bathroom_hazard_testing_results/zip_results.txt"
    
    # 4. Video Mode Config
    VIDEO_FILENAME = "messyPath.mp4"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if MODE == "image":
        image_path = os.path.join(script_dir, IMAGE_FILENAME)
        print(f"Mode: Single Image Analysis ({image_path})")
        
        # Ensure output dir exists
        os.makedirs(os.path.dirname(IMAGE_OUTPUT), exist_ok=True)
        
        try:
            result = detect_hazards(image_path)
            print_results(result)
            
            # Write to file for "easy viewing"
            with open(IMAGE_OUTPUT, 'a', encoding='utf-8') as f:
                log_result_to_file(f, result, IMAGE_FILENAME, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print(f"\nResult saved to {IMAGE_OUTPUT}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif MODE == "directory":
        dir_path = os.path.join(script_dir, IMAGE_DIR)
        output_path = os.path.join(script_dir, DIR_OUTPUT)
        process_directory_images(dir_path, output_file=output_path, poll_interval=POLL_INTERVAL)
        
    elif MODE == "batch":
        zip_path = os.path.join(script_dir, ZIP_FILENAME)
        output_path = os.path.join(script_dir, ZIP_OUTPUT)
        process_zip_images(zip_path, output_file=output_path, poll_interval=POLL_INTERVAL)
        
    elif MODE == "video":
        video_path = os.path.join(script_dir, VIDEO_FILENAME)
        process_video_continuous(video_path, poll_interval=POLL_INTERVAL)
    
    else:
        print(f"Error: Invalid MODE '{MODE}'")
        sys.exit(1)

if __name__ == "__main__":
    main()