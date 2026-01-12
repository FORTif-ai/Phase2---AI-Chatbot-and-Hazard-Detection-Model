import torch
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os
from pathlib import Path

# SAM 3 Imports
from sam3.model_builder import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor

# --- 1. CONFIGURATION ---
# Folder containing your test images
INPUT_DIR = Path("/home/akil/code/watai/sam3/test_image_inputs") 
# Folder where annotated results will be saved
OUTPUT_DIR = Path("/home/akil/code/watai/sam3/test_image_outputs_v2")

TEXT_PROMPTS = [
    "rug",                       # Direct match
    "floor carpet",              # Semantic alternative for rug
    "scattered household items", # Better for 'clutter_zone'
    "messy pile of objects",     # Alternative for 'clutter_zone'
    "electric wire",             # More specific than just 'wire'
    "thin black power cable",    # Helps SAM 3 identify thin structures
    "floor transition strip",    # Descriptive for 'uneven_threshold'
    "doorway threshold",         # Contextual for 'uneven_threshold'
    "household furniture",       # General category
    "chair and table",           # Specific instances of furniture
    "staircase",                 # Direct match
    "flight of stairs"           # Semantic alternative
    "single step"
]
CONFIDENCE_THRESHOLD = 0.15
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# --- 2. HELPER FUNCTIONS ---

def show_mask(mask, ax, color):
    """Overlay a mask with a specific color."""
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * np.array(color).reshape(1, 1, -1)
    ax.imshow(mask_image)

def show_box(box, ax, color, label, score):
    """Draw bounding box and label."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor=color[:3], facecolor='none', lw=2))
    ax.text(x0, y0 - 5, f"{label} {score:.2f}", 
            fontsize=10, color='white', weight='bold',
            bbox=dict(facecolor=color[:3], alpha=0.7, edgecolor='none', pad=1.5))

# --- 3. MAIN BATCH PROCESS ---

def main():
    # Setup Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Initialize Model & Processor
    print("Loading SAM 3 model...")
    model = build_sam3_image_model()
    model.to(device)
    processor = Sam3Processor(model)

    # Ensure Output Directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get list of images
    image_files = [f for f in INPUT_DIR.iterdir() if f.suffix.lower() in IMG_EXTENSIONS]
    print(f"Found {len(image_files)} images to process.")

    for img_path in image_files:
        print(f"Processing: {img_path.name}...")
        
        try:
            # Load Image
            image = Image.open(img_path).convert("RGB")
            
            # Initialize state (Embedding generation)
            inference_state = processor.set_image(image)

            # Store results for visualization
            all_results = []
            for prompt in TEXT_PROMPTS:
                output = processor.set_text_prompt(state=inference_state, prompt=prompt)
                if len(output["scores"]) > 0:
                    all_results.append({
                        "label": prompt,
                        "masks": output["masks"],
                        "boxes": output["boxes"],
                        "scores": output["scores"]
                    })

            # Visualization Logic
            fig = plt.figure(figsize=(12, 12))
            plt.imshow(image)
            ax = plt.gca()
            cmap = plt.get_cmap('tab10') 

            for i, result in enumerate(all_results):
                label = result["label"]
                color = cmap(i % 10) 

                for mask, box, score in zip(result["masks"], result["boxes"], result["scores"]):
                    score_val = score.item()
                    if score_val > CONFIDENCE_THRESHOLD:
                        show_mask(mask.cpu().numpy(), ax, color)
                        show_box(box.cpu().numpy(), ax, color, label, score_val)

            plt.axis('off')
            plt.title(f"SAM 3 Detection: {img_path.name}")
            
            # Save the figure
            save_path = OUTPUT_DIR / f"annotated_{img_path.name}"
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
            
            # Clean up memory to prevent slowdowns over large batches
            plt.close(fig)
            
        except Exception as e:
            print(f"Error processing {img_path.name}: {e}")

    print(f"\nBatch processing complete. Results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()