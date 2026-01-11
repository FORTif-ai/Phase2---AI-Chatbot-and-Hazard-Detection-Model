# example_test.py
"""
Simple example demonstrating how to test hazard detection with real images.
This is a minimal example you can modify for your own testing.
"""

from hazard_detector import detect_hazards, print_results

# Example 1: Test a single image
def example_single_image():
    """Test hazard detection on a single image."""
    image_path = "image.png"  # Change this to your image path
    
    print("Example 1: Testing a single image")
    print(f"Image: {image_path}\n")
    
    try:
        result = detect_hazards(image_path)
        print_results(result)
        
        # Access specific data
        if result.get("hazard_detected"):
            print("\n⚠️  Hazards found!")
            for hazard in result.get("hazards", []):
                print(f"  - {hazard.get('type')} at {hazard.get('location')} (Severity: {hazard.get('severity')})")
        else:
            print("\n✅ No hazards detected")
            
    except FileNotFoundError:
        print(f"Error: Image '{image_path}' not found. Please update the path.")
    except Exception as e:
        print(f"Error: {e}")


# Example 2: Test multiple images programmatically
def example_multiple_images():
    """Test hazard detection on multiple images."""
    image_paths = [
        "image.png",  # Add your image paths here
        # "test1.jpg",
        # "test2.jpg",
    ]
    
    print("\n" + "="*70)
    print("Example 2: Testing multiple images")
    print("="*70 + "\n")
    
    results = []
    for image_path in image_paths:
        try:
            print(f"Testing: {image_path}")
            result = detect_hazards(image_path)
            results.append((image_path, result))
            
            # Quick summary
            hazard = result.get("hazard_detected", False)
            people = result.get("people_detected", False)
            print(f"  People: {'Yes' if people else 'No'}, Hazards: {'Yes' if hazard else 'No'}\n")
            
        except FileNotFoundError:
            print(f"  ⚠️  Image not found: {image_path}\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    # Summary
    print("="*70)
    print("Summary:")
    print(f"  Total images tested: {len(results)}")
    print(f"  Images with hazards: {sum(1 for _, r in results if r.get('hazard_detected', False))}")
    print(f"  Images with people: {sum(1 for _, r in results if r.get('people_detected', False))}")
    print("="*70)


if __name__ == "__main__":
    print("="*70)
    print("Hazard Detection - Example Test Script")
    print("="*70)
    print("\nThis script demonstrates how to test hazard detection.")
    print("Modify the image paths to test with your own images.\n")
    
    # Run examples
    example_single_image()
    example_multiple_images()
    
    print("\n" + "="*70)
    print("Tip: Use 'python test_with_images.py --help' for more testing options")
    print("="*70)


