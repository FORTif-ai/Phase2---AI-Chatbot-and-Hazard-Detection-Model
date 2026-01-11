# Testing Guide: Hazard Detection with Real Images

This guide explains how to test the hazard detection functionality using real images.

## Quick Start

### Option 1: Test a Single Image (Easiest)

1. **Place your image** in the project folder (or use full path)
2. **Run the test script**:
   ```bash
   python test_with_images.py your_image.jpg
   ```

### Option 2: Test Multiple Images from a Directory

1. **Create a folder** with your test images (e.g., `test_images/`)
2. **Run the test script**:
   ```bash
   python test_with_images.py --dir test_images
   ```

### Option 3: Test and Save Results to File

```bash
python test_with_images.py --dir test_images --output test_results.txt
```

## Detailed Usage

### Using `test_with_images.py` (Recommended)

This script provides an easy way to test with real images:

#### Test Single Image
```bash
# Basic usage
python test_with_images.py path/to/image.jpg

# Quiet mode (minimal output)
python test_with_images.py path/to/image.jpg --quiet

# Verbose mode (detailed output)
python test_with_images.py path/to/image.jpg --verbose
```

#### Test Directory of Images
```bash
# Test all images in a directory
python test_with_images.py --dir path/to/images

# Save results to file
python test_with_images.py --dir path/to/images --output results.txt

# Verbose output for each image
python test_with_images.py --dir path/to/images --verbose
```

**Supported image formats:**
- `.jpg` / `.jpeg`
- `.png`
- `.gif`
- `.bmp`
- `.webp`

### Using `test_single_image.py`

For testing a single image with automatic documentation:

```bash
python test_single_image.py
```

This will test `image.png` in the project root and save results to `testing_documentation/hallway_images.txt`.

To test a different image, edit `test_single_image.py` and change the `image_path` variable.

### Using `hazard_detector.py` Directly

#### Single Image Mode

1. Edit `hazard_detector.py`:
   ```python
   MODE = "image"
   IMAGE_FILENAME = "your_image.jpg"
   ```

2. Run:
   ```bash
   python hazard_detector.py
   ```

#### Batch Mode (from Zip File)

1. Create a zip file containing your images (JPG/JPEG only)
2. Edit `hazard_detector.py`:
   ```python
   MODE = "batch"
   ZIP_FILENAME = "your_images.zip"
   OUTPUT_FILE = "testing_documentation/hallway_images.txt"
   ```

3. Run:
   ```bash
   python hazard_detector.py
   ```

## Programmatic Usage

You can also use the detection function directly in your own Python code:

```python
from hazard_detector import detect_hazards, print_results

# Test a single image
result = detect_hazards("path/to/image.jpg")

# Print formatted results
print_results(result)

# Access data directly
if result.get("hazard_detected"):
    for hazard in result.get("hazards", []):
        print(f"Found {hazard['type']} at {hazard['location']}")
        print(f"Severity: {hazard['severity']}")
```

## Testing Workflow

### Step 1: Prepare Your Images

- Collect real images of hallways, rooms, or areas where you want to detect hazards
- Images should contain:
  - People (optional, but recommended for realistic testing)
  - Potential hazards (wet floors, obstacles, cables, etc.)
  - Clear, well-lit scenes work best

### Step 2: Test Individual Images

Start by testing a few images individually to understand the detection quality:

```bash
python test_with_images.py test1.jpg
python test_with_images.py test2.jpg
python test_with_images.py test3.jpg
```

### Step 3: Batch Test

Once you're confident, test all images at once:

```bash
python test_with_images.py --dir test_images --output batch_results.txt
```

### Step 4: Review Results

- Check console output for immediate feedback
- Review saved output files for detailed analysis
- Compare results across different images to understand detection patterns

## Understanding Results

The detection results include:

- **People Detected**: Whether people are present in the image
- **Hazard Detected**: Whether any hazards were found
- **Hazards Array**: List of detected hazards, each with:
  - `type`: What the hazard is (e.g., "wet floor", "loose cable")
  - `location`: Where it is (e.g., "left side of hallway", "near entrance")
  - `severity`: Risk level (`low`, `medium`, or `high`)
  - `details`: Additional context
  - `sms_text`: Concise alert text for notifications
- **Summary**: Brief description of the scene

## Tips for Better Testing

1. **Test with variety**: Include images with and without hazards, with and without people
2. **Test edge cases**: Very cluttered scenes, dim lighting, unusual angles
3. **Check rate limits**: The free Gemini API tier allows 15 requests per minute
4. **Save results**: Use `--output` to document your tests for later review
5. **Compare results**: Test the same image multiple times to check consistency

## Example Test Scenarios

### Scenario 1: Quick Single Image Test
```bash
# Test one image quickly
python test_with_images.py hallway1.jpg
```

### Scenario 2: Comprehensive Directory Test
```bash
# Test all images in a folder and save detailed results
python test_with_images.py --dir ./test_images --output comprehensive_test.txt --verbose
```

### Scenario 3: Quick Batch Test
```bash
# Test all images with summary only
python test_with_images.py --dir ./test_images
```

## Troubleshooting

**"Image not found" error:**
- Check the file path is correct
- Use absolute paths if relative paths don't work
- Ensure the image file exists and is readable

**"GEMINI_API_KEY not found" error:**
- Make sure you have a `.env` file with `GEMINI_API_KEY=your_key_here`
- Or set the environment variable directly

**Rate limit errors:**
- The free tier allows 15 requests per minute
- Wait a minute between batches if you hit the limit
- The scripts automatically add delays for batch processing

**Poor detection results:**
- Ensure images are clear and well-lit
- Try different angles or closer shots
- Check that hazards are visible and not too small in the image

## Next Steps

After testing with real images:

1. **Analyze results**: Review which hazards were detected correctly
2. **Refine prompts**: Adjust the `HAZARD_PROMPT` in `hazard_detector.py` if needed
3. **Test edge cases**: Try challenging scenarios
4. **Document findings**: Keep notes on what works well and what doesn't


