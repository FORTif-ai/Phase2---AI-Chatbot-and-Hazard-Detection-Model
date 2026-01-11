# Hazard Detection using Gemini AI

This Python program analyzes camera footage (images) to detect hazards near people using Google's Gemini AI.

## How to Get a Gemini API Key

Follow these exact steps to obtain your Gemini API key:

### Step 1: Go to Google AI Studio
1. Open your web browser and navigate to: **https://aistudio.google.com/**
2. Sign in with your Google account (create one if you don't have it)

### Step 2: Get Your API Key
1. Once signed in, click on **"Get API key"** button in the left sidebar (or top navigation)
2. You'll see a page titled "API keys"
3. Click on **"Create API key"** button
4. You'll see two options:
   - **"Create API key in new project"** - Choose this if you don't have an existing Google Cloud project
   - **"Create API key in existing project"** - Choose this if you want to use an existing project
5. Select your preferred option (most people will choose "Create API key in new project")
6. Your API key will be generated and displayed
7. **IMPORTANT**: Click the **copy button** to copy your API key and save it somewhere safe
   - You won't be able to see the full key again after you close this dialog
   - Keep it secret - don't share it publicly or commit it to version control

### Step 3: Note About Free Tier
- Gemini API offers a generous free tier
- Free tier includes: 15 requests per minute, 1 million tokens per minute, 1,500 requests per day
- This is usually more than enough for testing and small projects
- You can check current pricing at: https://ai.google.dev/pricing

## Installation

1. Create a virtual environment (recommended on macOS):
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. The `.env` file with your API key has already been created! The program will automatically load it.

**Note:** Remember to activate the virtual environment (`source venv/bin/activate`) each time you open a new terminal session before running the program.

## Usage

The program supports three modes: **image**, **video**, and **batch**. Change the `MODE` variable in `hazard_detector.py` to switch between modes.

### Mode 1: Single Image Analysis

1. **Put your image** in the HazardDetection folder (same folder as `hazard_detector.py`)

2. **Edit the settings** in `hazard_detector.py`:
   - Set `MODE = "image"`
   - Set `IMAGE_FILENAME = "your_image.jpg"` (change to your actual image filename)

3. **Run the program**:
```bash
source venv/bin/activate
python hazard_detector.py
```

### Mode 2: Video Analysis

1. **Put your video file** in the HazardDetection folder

2. **Edit the settings** in `hazard_detector.py`:
   - Set `MODE = "video"`
   - Set `VIDEO_FILENAME = "your_video.mp4"` (change to your actual video filename)
   - Set `POLL_INTERVAL = 4.0` (seconds between frame analyses)

3. **Run the program**:
```bash
source venv/bin/activate
python hazard_detector.py
```

### Mode 3: Batch Processing from Zip File

Process multiple hallway images from a zip file and document results:

1. **Create a zip file** containing your JPG images:
   - Name it `hallway_images.zip` (or change `ZIP_FILENAME` in the code)
   - Place it in the HazardDetection folder
   - Include only JPG/JPEG files in the zip

2. **Edit the settings** in `hazard_detector.py`:
   - Set `MODE = "batch"`
   - Set `ZIP_FILENAME = "hallway_images.zip"` (or your zip filename)
   - Set `OUTPUT_FILE = "testing_documentation/hallway_images.txt"` (where results will be saved)
   - Set `POLL_INTERVAL = 4.0` (seconds between image analyses to respect API rate limits)

3. **Run the program**:
```bash
source venv/bin/activate
python hazard_detector.py
```

4. **Results** will be written to `testing_documentation/hallway_images.txt` with:
   - Test date and metadata
   - Detailed analysis for each image
   - Hazard detection results (type, location, severity)
   - Summary information

### Example: Batch Processing
If you have a zip file named `my_hallway_images.zip`:
1. Put `my_hallway_images.zip` in the HazardDetection folder
2. Set `MODE = "batch"` and `ZIP_FILENAME = "my_hallway_images.zip"`
3. Run: `python hazard_detector.py`
4. Check `testing_documentation/hallway_images.txt` for results

### Testing with Real Images (Recommended)

The easiest way to test with real images is using `test_with_images.py`:

**Test a single image:**
```bash
python test_with_images.py your_image.jpg
```

**Test all images in a directory:**
```bash
python test_with_images.py --dir test_images
```

**Test directory and save results:**
```bash
python test_with_images.py --dir test_images --output results.txt
```

**Get help:**
```bash
python test_with_images.py --help
```

For more detailed testing instructions, see `TESTING_GUIDE.md`.

### Sample Output
```
Analyzing image for hazards...

============================================================
HAZARD DETECTION RESULTS
============================================================

People Detected: Yes
Hazard Detected: Yes

Number of Hazards Found: 2

Hazard Details:

  Hazard #1:
    Type: Wet floor
    Location: Near person's feet, left side of image
    Severity: high
    Details: Slippery surface that could cause falls

  Hazard #2:
    Type: Loose cable
    Location: On the ground, center of frame
    Severity: medium
    Details: Trip hazard extending across walkway

Summary: Image shows a person walking in an office environment with a wet floor and loose cable present, both posing fall and trip hazards.

============================================================
```

## Programmatic Usage

You can also import and use the detector in your own Python code:

```python
from hazard_detector import detect_hazards, print_results

# Analyze an image
result = detect_hazards('path/to/image.jpg', api_key='your-api-key')

# Print formatted results
print_results(result)

# Or access the data directly
if result['hazard_detected']:
    for hazard in result['hazards']:
        print(f"Found {hazard['type']} at {hazard['location']}")
```

## Features

- ✅ Detects hazards in images using Gemini AI vision capabilities
- ✅ Identifies location and type of hazards
- ✅ Assesses severity levels (low/medium/high)
- ✅ Detects presence of people in the scene
- ✅ Provides structured JSON output
- ✅ Command-line interface for easy testing
- ✅ Can be imported as a module for integration into other projects
- ✅ Batch processing from zip files with automatic documentation
- ✅ Video frame analysis with configurable polling intervals
- ✅ SMS alerts via Twilio (optional, requires Twilio credentials)

## Supported Image Formats

The program supports common image formats including:
- JPEG/JPG
- PNG
- GIF
- BMP
- WebP

## Troubleshooting

**Error: "No API key provided"**
- Make sure you've set the GEMINI_API_KEY environment variable
- Or pass the api_key parameter directly to the detect_hazards() function

**Error: "Image not found"**
- Check that the image path is correct
- Use absolute paths if relative paths aren't working

**API Rate Limits**
- If you hit rate limits, wait a minute and try again
- Free tier allows 15 requests per minute

