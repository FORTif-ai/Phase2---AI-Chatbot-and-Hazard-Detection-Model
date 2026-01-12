import cv2
from ultralytics import YOLO
from pathlib import Path

# --- 1. CONFIGURATION ---
SCRIPT_DIR = Path(__file__).resolve().parent

# --- 2. UPDATED PATHS ---
# Specify the FOLDER containing your test images
TEST_IMAGES_DIR = SCRIPT_DIR / "runs" / "detect"/ "test_image_inputs"  # <-- CHANGE THIS to your input folder

# Where to save the resulting images
# All annotated images will be saved here
SAVE_DIR = SCRIPT_DIR / "batch_results_jan5"

# Path to your best-trained model weights
MODEL_PATH = SCRIPT_DIR / "runs" / "detect" / "stage2_finetune_all2" / "weights" / "best.pt"

# Confidence threshold
CONF_THRESHOLD = 0.5

# Supported image extensions
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# --- END OF CONFIGURATION ---

def run_batch_detection():
    """
    Iterates through a folder of images, runs YOLO detection, 
    and saves annotated versions to a separate directory.
    """
    
    # --- 1. Pre-run Checks ---
    if not MODEL_PATH.exists():
        print(f"Error: Model file not found at {MODEL_PATH}")
        return

    if not TEST_IMAGES_DIR.exists() or not TEST_IMAGES_DIR.is_dir():
        print(f"Error: Input directory not found at {TEST_IMAGES_DIR}")
        return

    # Create the save directory if it doesn't exist
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # --- 2. Load Model ---
    print(f"Loading model from {MODEL_PATH}...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # --- 3. Process Images ---
    # Find all files in the directory
    image_files = [f for f in TEST_IMAGES_DIR.iterdir() if f.suffix.lower() in IMG_EXTENSIONS]
    
    if not image_files:
        print(f"No valid images found in {TEST_IMAGES_DIR}")
        return

    print(f"Found {len(image_files)} images. Starting detection...")

    for img_path in image_files:
      print(f"Processing: {img_path.name}...", end=" ", flush=True)
      
      try:
          # 1. Run inference directly on the PATH, not the cv2 image
          # This is more memory efficient and avoids "double-loading" issues
          results = model(str(img_path), conf=CONF_THRESHOLD, verbose=False)
          
          # 2. Extract the first result (since we are passing one image at a time)
          res = results[0]

          # 3. Use .plot() to get the annotated image
          # Using labels=True/Boxes=True here ensures we control exactly what is drawn
          annotated_frame = res.plot()

          # 4. Save the Result using OpenCV
          save_path = SAVE_DIR / f"{img_path.stem}_annotated{img_path.suffix}"
          cv2.imwrite(str(save_path), annotated_frame)
          print(f"Done!")

      except Exception as e:
          print(f"Error processing {img_path.name}: {e}")

    print(f"\nBatch processing complete. All results saved to:\n{SAVE_DIR}")

if __name__ == "__main__":
    run_batch_detection()