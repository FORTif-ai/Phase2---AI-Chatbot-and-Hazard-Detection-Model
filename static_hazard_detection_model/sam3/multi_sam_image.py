import torch
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os

# SAM 3 Imports
from sam3.model_builder import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor

# --- Configuration ---
IMAGE_PATH = r"/home/akil/code/watai/sam3/test_image_inputs/spr-product-lorena-canals-reversible-washable-area-rug-dburreson-006-50e8479d3bbe44a7a5ec6dfd9f4056db.jpeg"
TEXT_PROMPTS = ["rug", "wire", "staircase", "furniture", "cluttered objects"]  # Add as many concepts as you want
CONFIDENCE_THRESHOLD = 0.15

def show_mask(mask, ax, color):
    """Overlay a mask with a specific color."""
    h, w = mask.shape[-2:]
    # Reshape mask and apply color (R, G, B, Alpha)
    mask_image = mask.reshape(h, w, 1) * np.array(color).reshape(1, 1, -1)
    ax.imshow(mask_image)

def show_box(box, ax, color, label, score):
    """Draw bounding box and label."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    
    # Draw box
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor=color[:3], facecolor='none', lw=2))
    
    # Draw Label background and text
    ax.text(x0, y0 - 5, f"{label} {score:.2f}", 
            fontsize=10, color='white', weight='bold',
            bbox=dict(facecolor=color[:3], alpha=0.7, edgecolor='none', pad=1.5))

def main():
    # 1. Initialize Model
    print("Loading SAM 3 model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_sam3_image_model()
    model.to(device)
    processor = Sam3Processor(model)

    # 2. Load Image
    if not os.path.exists(IMAGE_PATH):
        print(f"Image not found: {IMAGE_PATH}")
        return
    image = Image.open(IMAGE_PATH).convert("RGB")
    
    # Initialize inference state once (expensive operation, do it once per image)
    inference_state = processor.set_image(image)

    # 3. Run Inference for EACH prompt
    all_results = []
    
    print(f"Processing prompts: {TEXT_PROMPTS}")
    for prompt in TEXT_PROMPTS:
        output = processor.set_text_prompt(state=inference_state, prompt=prompt)
        
        # Store results along with the label name
        if len(output["scores"]) > 0:
            all_results.append({
                "label": prompt,
                "masks": output["masks"],  # (N, H, W)
                "boxes": output["boxes"],  # (N, 4)
                "scores": output["scores"] # (N,)
            })

    # 4. Visualization
    plt.figure(figsize=(12, 12))
    plt.imshow(image)
    ax = plt.gca()

    # Generate distinct colors for each class prompt
    # We use a colormap to ensure distinct colors for "rug", "wire", etc.
    cmap = plt.get_cmap('tab10') 
    
    found_objects = False
    
    for i, result in enumerate(all_results):
        label = result["label"]
        # Assign a unique color for this class index
        color = cmap(i % 10) # returns (r,g,b,a)

        for mask, box, score in zip(result["masks"], result["boxes"], result["scores"]):
            score_val = score.item()
            
            if score_val > CONFIDENCE_THRESHOLD:
                found_objects = True
                # Convert tensors to numpy
                mask_np = mask.cpu().numpy()
                box_np = box.cpu().numpy()
                
                show_mask(mask_np, ax, color)
                show_box(box_np, ax, color, label, score_val)

    plt.axis('off')
    plt.title(f"SAM 3 Detection: {', '.join(TEXT_PROMPTS)}")
    
    if not found_objects:
        print("No objects found above threshold.")
    else:
        print("Visualization generated.")
        
    plt.show()

if __name__ == "__main__":
    main()