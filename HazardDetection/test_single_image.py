# test_single_image.py
"""Script to test hazard detection on a single image and document results."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from hazard_detector import detect_hazards, print_results

load_dotenv()

def test_image_and_document(image_path: str, output_file: str = "testing_documentation/hallway_images.txt"):
    """
    Test hazard detection on a single image and document results.
    
    Args:
        image_path: Path to the image file
        output_file: Path to the output text file for documenting results
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Testing image: {image_path}")
    print(f"Results will be written to: {output_file}\n")
    
    # Analyze image
    print("Analyzing image for hazards...")
    try:
        result = detect_hazards(image_path)
        
        # Print results to console
        print_results(result)
        
        # Write results to file
        file_exists = os.path.exists(output_file)
        with open(output_file, 'a', encoding='utf-8') as f:
            # Write header if file is new
            if not file_exists:
                f.write("=" * 80 + "\n")
                f.write("HALLWAY IMAGE HAZARD DETECTION TEST RESULTS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
            
            # Write results for this image
            f.write(f"\n{'=' * 80}\n")
            f.write(f"IMAGE: {os.path.basename(image_path)}\n")
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
                
                f.write(f"People Detected: {'Yes' if people else 'No'}\n")
                f.write(f"Hazard Detected: {'Yes' if hazard else 'No'}\n")
                f.write(f"Summary: {summary}\n\n")
                
                if hazards:
                    f.write(f"Hazards Found: {len(hazards)}\n")
                    for i, h in enumerate(hazards, 1):
                        f.write(f"\n  Hazard #{i}:\n")
                        f.write(f"    Type: {h.get('type', 'N/A')}\n")
                        f.write(f"    Location: {h.get('location', 'N/A')}\n")
                        f.write(f"    Severity: {h.get('severity', 'N/A')}\n")
                        f.write(f"    Details: {h.get('details', 'N/A')}\n")
                        f.write(f"    SMS Text: {h.get('sms_text', 'N/A')}\n")
                else:
                    f.write("Hazards Found: 0\n")
                    f.write("Status: No obstacles or hazards detected.\n")
            
            f.write("\n")
        
        print(f"\n{'=' * 60}")
        print(f"Results documented in: {output_file}")
        print(f"{'=' * 60}")
        
        return result
        
    except Exception as e:
        error_msg = f"Error analyzing image: {e}"
        print(f"ERROR: {error_msg}")
        
        # Write error to file
        file_exists = os.path.exists(output_file)
        with open(output_file, 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write("=" * 80 + "\n")
                f.write("HALLWAY IMAGE HAZARD DETECTION TEST RESULTS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
            
            f.write(f"\n{'=' * 80}\n")
            f.write(f"IMAGE: {os.path.basename(image_path)}\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"ERROR: {error_msg}\n\n")
        
        raise


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "image.png")
    output_file = os.path.join(script_dir, "testing_documentation", "hallway_images.txt")
    
    try:
        result = test_image_and_document(image_path, output_file)
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        if result.get("parsed") is not False:
            print(f"People Detected: {'Yes' if result.get('people_detected') else 'No'}")
            print(f"Hazard Detected: {'Yes' if result.get('hazard_detected') else 'No'}")
            if result.get("hazards"):
                print(f"Number of Hazards: {len(result.get('hazards', []))}")
            print(f"Summary: {result.get('summary', 'N/A')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

