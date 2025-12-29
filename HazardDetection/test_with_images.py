# test_with_images.py
"""
Simple script to test hazard detection with real images.
Supports testing single images or entire directories of images.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from hazard_detector import detect_hazards, print_results

load_dotenv()

def test_single_image(image_path: str, verbose: bool = True):
    """
    Test hazard detection on a single image.
    
    Args:
        image_path: Path to the image file
        verbose: If True, print detailed results
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    print(f"\n{'='*70}")
    print(f"Testing: {os.path.basename(image_path)}")
    print(f"Full path: {image_path}")
    print(f"{'='*70}\n")
    
    try:
        result = detect_hazards(image_path)
        
        if verbose:
            print_results(result)
        else:
            # Quick summary
            hazard = result.get("hazard_detected", False)
            people = result.get("people_detected", False)
            num_hazards = len(result.get("hazards", []))
            
            print(f"People: {'Yes' if people else 'No'}")
            print(f"Hazards: {'Yes' if hazard else 'No'} ({num_hazards} found)")
            if result.get("summary"):
                print(f"Summary: {result.get('summary')}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        raise


def test_directory(directory_path: str, output_file: str = None, verbose: bool = False):
    """
    Test hazard detection on all images in a directory.
    
    Args:
        directory_path: Path to directory containing images
        output_file: Optional path to save results (if None, prints to console only)
        verbose: If True, print detailed results for each image
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    # Find all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(Path(directory_path).glob(f"*{ext}"))
        image_files.extend(Path(directory_path).glob(f"*{ext.upper()}"))
    
    if not image_files:
        print(f"No image files found in: {directory_path}")
        print(f"Supported formats: {', '.join(image_extensions)}")
        return
    
    print(f"\n{'='*70}")
    print(f"Testing {len(image_files)} image(s) from: {directory_path}")
    print(f"{'='*70}\n")
    
    results = []
    output_lines = []
    
    if output_file:
        output_lines.append("=" * 80)
        output_lines.append("HAZARD DETECTION TEST RESULTS - BATCH TESTING")
        output_lines.append("=" * 80)
        output_lines.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"Directory: {directory_path}")
        output_lines.append(f"Total Images: {len(image_files)}")
        output_lines.append("=" * 80)
        output_lines.append("")
    
    for idx, image_path in enumerate(sorted(image_files), 1):
        print(f"\n[{idx}/{len(image_files)}] Processing: {image_path.name}")
        
        try:
            result = test_single_image(str(image_path), verbose=verbose)
            results.append((str(image_path), result))
            
            # Add to output file if specified
            if output_file:
                output_lines.append(f"\n{'='*80}")
                output_lines.append(f"IMAGE #{idx}: {image_path.name}")
                output_lines.append(f"{'='*80}")
                output_lines.append(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                output_lines.append("")
                
                if result.get("parsed") is False:
                    output_lines.append("ERROR: Could not parse JSON response.")
                    output_lines.append(f"Raw Response: {result.get('raw_response', 'N/A')}")
                else:
                    people = result.get("people_detected", False)
                    hazard = result.get("hazard_detected", False)
                    hazards = result.get("hazards", [])
                    summary = result.get("summary", "N/A")
                    
                    output_lines.append(f"People Detected: {'Yes' if people else 'No'}")
                    output_lines.append(f"Hazard Detected: {'Yes' if hazard else 'No'}")
                    output_lines.append(f"Summary: {summary}")
                    output_lines.append("")
                    
                    if hazards:
                        output_lines.append(f"Hazards Found: {len(hazards)}")
                        for i, h in enumerate(hazards, 1):
                            output_lines.append(f"\n  Hazard #{i}:")
                            output_lines.append(f"    Type: {h.get('type', 'N/A')}")
                            output_lines.append(f"    Location: {h.get('location', 'N/A')}")
                            output_lines.append(f"    Severity: {h.get('severity', 'N/A')}")
                            output_lines.append(f"    Details: {h.get('details', 'N/A')}")
                            output_lines.append(f"    SMS Text: {h.get('sms_text', 'N/A')}")
                    else:
                        output_lines.append("Hazards Found: 0")
                        output_lines.append("Status: No obstacles or hazards detected.")
                
                output_lines.append("")
        
        except Exception as e:
            error_msg = f"Error analyzing {image_path.name}: {e}"
            print(f"ERROR: {error_msg}")
            results.append((str(image_path), {"error": str(e)}))
            
            if output_file:
                output_lines.append(f"\n{'='*80}")
                output_lines.append(f"IMAGE #{idx}: {image_path.name}")
                output_lines.append(f"{'='*80}")
                output_lines.append(f"ERROR: {error_msg}")
                output_lines.append("")
    
    # Write output file if specified
    if output_file:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        output_lines.append("\n" + "=" * 80)
        output_lines.append("END OF TEST RESULTS")
        output_lines.append("=" * 80)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))
        
        print(f"\n{'='*70}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*70}")
    
    # Print summary
    print(f"\n{'='*70}")
    print("BATCH TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total images tested: {len(results)}")
    
    successful = sum(1 for _, r in results if "error" not in r)
    with_hazards = sum(1 for _, r in results if r.get("hazard_detected", False))
    with_people = sum(1 for _, r in results if r.get("people_detected", False))
    
    print(f"Successfully analyzed: {successful}")
    print(f"Images with hazards: {with_hazards}")
    print(f"Images with people: {with_people}")
    print(f"{'='*70}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test hazard detection with real images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a single image
  python test_with_images.py image.jpg
  
  # Test a single image (quiet mode)
  python test_with_images.py image.jpg --quiet
  
  # Test all images in a directory
  python test_with_images.py --dir ./test_images
  
  # Test directory and save results to file
  python test_with_images.py --dir ./test_images --output results.txt
  
  # Test directory with verbose output
  python test_with_images.py --dir ./test_images --verbose
        """
    )
    
    parser.add_argument(
        "image_path",
        nargs="?",
        help="Path to a single image file to test"
    )
    
    parser.add_argument(
        "--dir",
        dest="directory",
        help="Path to directory containing images to test"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        help="Path to output file for batch results (only used with --dir)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed results for each image (default: summary only for batch)"
    )
    
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Print minimal output (only for single image mode)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment variables.")
        print("Please set it in your .env file or as an environment variable.")
        sys.exit(1)
    
    try:
        if args.directory:
            # Test directory
            test_directory(
                args.directory,
                output_file=args.output_file,
                verbose=args.verbose
            )
        elif args.image_path:
            # Test single image
            test_single_image(
                args.image_path,
                verbose=not args.quiet
            )
        else:
            parser.print_help()
            print("\nERROR: Please provide either an image path or --dir option")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


