# generate_video.py
"""
Script to generate a video of a senior individual walking through a cluttered hallway.
Uses AI image generation to create frames and combines them into an MP4 video.
"""

import os
import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv
import time

load_dotenv()

def generate_frame_with_gemini(prompt: str, frame_number: int, api_key: str) -> Image.Image:
    """
    Generate a single frame using Gemini's image generation capabilities.
    Note: Gemini may not have direct image generation, so we'll use an alternative approach.
    """
    # For now, we'll create a placeholder that can be replaced with actual AI generation
    # You can integrate with services like DALL-E, Stable Diffusion, or other image generation APIs
    
    # Placeholder: Create a synthetic frame
    # In production, replace this with actual AI image generation
    width, height = 1920, 1080
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create a hallway-like background
    frame[:, :] = (200, 200, 200)  # Light gray hallway
    
    # Add some objects (clutter) - represented as colored rectangles
    np.random.seed(frame_number)
    num_objects = 15 + np.random.randint(0, 10)  # More objects than messyPath
    
    for i in range(num_objects):
        x = np.random.randint(0, width - 100)
        y = np.random.randint(0, height - 100)
        w = np.random.randint(50, 150)
        h = np.random.randint(50, 150)
        color = tuple(np.random.randint(50, 200, 3).tolist())
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, -1)
    
    # Add a person silhouette (senior individual) - represented as a simple shape
    person_x = int(width * 0.3 + frame_number * 5)  # Person moves forward
    person_y = int(height * 0.6)
    person_w, person_h = 80, 180
    
    # Person body
    cv2.rectangle(frame, 
                  (person_x - person_w//2, person_y - person_h),
                  (person_x + person_w//2, person_y),
                  (100, 100, 150), -1)
    
    # Person head
    cv2.circle(frame, (person_x, person_y - person_h - 20), 25, (100, 100, 150), -1)
    
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def generate_video_using_ai_images(output_path: str = "seniorClutteredHallway.mp4", 
                                   num_frames: int = 120,
                                   fps: int = 30,
                                   api_key: str = None):
    """
    Generate a video by creating AI-generated frames and combining them.
    
    Args:
        output_path: Path to save the output video
        num_frames: Number of frames to generate
        fps: Frames per second for the output video
        api_key: Optional API key for image generation service
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"Generating {num_frames} frames for video: {output_path}")
    print("This may take a while...")
    
    # Create temporary directory for frames
    temp_dir = "temp_frames"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Generate frames
        frames = []
        for i in range(num_frames):
            print(f"Generating frame {i+1}/{num_frames}...", end='\r')
            
            prompt = f"A senior elderly person walking through a very cluttered hallway with many objects, boxes, and items scattered around. Frame {i} of a walking sequence. The person is moving forward through the hallway. The hallway has more clutter and objects than a typical messy hallway."
            
            # Generate frame (placeholder implementation)
            frame_img = generate_frame_with_gemini(prompt, i, api_key)
            frame_path = os.path.join(temp_dir, f"frame_{i:04d}.jpg")
            frame_img.save(frame_path)
            frames.append(frame_path)
        
        print(f"\nAll frames generated. Creating video...")
        
        # Read first frame to get dimensions
        first_frame = cv2.imread(frames[0])
        height, width, layers = first_frame.shape
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Write frames to video
        for frame_path in frames:
            frame = cv2.imread(frame_path)
            video_writer.write(frame)
        
        video_writer.release()
        print(f"Video created successfully: {output_path}")
        
    finally:
        # Clean up temporary frames
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("Temporary files cleaned up.")


def generate_video_advanced(output_path: str = "seniorClutteredHallway.mp4",
                            duration_seconds: float = 4.0,
                            fps: int = 30,
                            width: int = 1920,
                            height: int = 1080):
    """
    Generate a more realistic video using OpenCV with better graphics.
    Creates a cluttered hallway scene with a senior person walking through.
    """
    print(f"Generating video: {output_path}")
    print(f"Duration: {duration_seconds}s, FPS: {fps}, Resolution: {width}x{height}")
    
    num_frames = int(duration_seconds * fps)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Define hallway objects (more than messyPath)
    hallway_objects = []
    np.random.seed(42)  # For reproducibility
    
    # Create many objects scattered in the hallway
    for i in range(25):  # More objects than typical messy hallway
        obj = {
            'x': np.random.randint(0, width),
            'y': np.random.randint(0, height),
            'width': np.random.randint(40, 120),
            'height': np.random.randint(40, 120),
            'color': tuple(np.random.randint(30, 180, 3).tolist()),
            'type': np.random.choice(['box', 'bag', 'item'])
        }
        hallway_objects.append(obj)
    
    # Person starting position
    person_start_x = int(width * 0.1)
    person_y = int(height * 0.65)
    person_speed = width / (num_frames * 0.8)  # Person moves across 80% of video
    
    for frame_num in range(num_frames):
        # Create frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Draw hallway background (perspective effect)
        # Floor
        floor_color = (180, 180, 180)
        cv2.rectangle(frame, (0, int(height * 0.7)), (width, height), floor_color, -1)
        
        # Walls
        wall_color = (220, 220, 220)
        cv2.rectangle(frame, (0, 0), (width, int(height * 0.7)), wall_color, -1)
        
        # Add perspective lines (hallway depth)
        for i in range(5):
            y = int(height * 0.7 + i * (height * 0.3 / 5))
            x1 = int(width * 0.2 - i * 50)
            x2 = int(width * 0.8 + i * 50)
            cv2.line(frame, (x1, y), (x2, y), (160, 160, 160), 1)
        
        # Draw hallway objects (clutter)
        for obj in hallway_objects:
            x, y = obj['x'], obj['y']
            w, h = obj['width'], obj['height']
            color = obj['color']
            
            # Only draw if object is in visible area
            if 0 <= x < width and 0 <= y < height:
                if obj['type'] == 'box':
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, -1)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 2)
                elif obj['type'] == 'bag':
                    cv2.ellipse(frame, (x + w//2, y + h//2), (w//2, h//2), 0, 0, 360, color, -1)
                else:
                    cv2.circle(frame, (x + w//2, y + h//2), w//2, color, -1)
        
        # Draw senior person (walking animation)
        person_x = int(person_start_x + frame_num * person_speed)
        
        if person_x < width:
            # Person body (slightly hunched posture for senior)
            body_width = 70
            body_height = 160
            body_top = person_y - body_height
            body_bottom = person_y
            
            # Body
            cv2.rectangle(frame,
                         (person_x - body_width//2, body_top),
                         (person_x + body_width//2, body_bottom),
                         (80, 80, 120), -1)
            
            # Head (slightly forward for senior posture)
            head_radius = 22
            head_x = person_x
            head_y = body_top - head_radius - 5
            cv2.circle(frame, (head_x, head_y), head_radius, (80, 80, 120), -1)
            
            # Walking legs (alternating)
            leg_offset = 15 if (frame_num // 5) % 2 == 0 else -15
            leg_width = 25
            leg_height = 80
            
            # Left leg
            cv2.rectangle(frame,
                         (person_x - body_width//4 - leg_width//2, body_bottom),
                         (person_x - body_width//4 + leg_width//2, body_bottom + leg_height + leg_offset),
                         (60, 60, 100), -1)
            
            # Right leg
            cv2.rectangle(frame,
                         (person_x + body_width//4 - leg_width//2, body_bottom),
                         (person_x + body_width//4 + leg_width//2, body_bottom + leg_height - leg_offset),
                         (60, 60, 100), -1)
            
            # Arms (walking motion)
            arm_offset = 20 if (frame_num // 5) % 2 == 0 else -20
            arm_width = 20
            arm_length = 60
            
            # Left arm
            cv2.rectangle(frame,
                         (person_x - body_width//2 - arm_length, body_top + 30),
                         (person_x - body_width//2, body_top + 30 + arm_width),
                         (70, 70, 110), -1)
            
            # Right arm
            cv2.rectangle(frame,
                         (person_x + body_width//2, body_top + 30),
                         (person_x + body_width//2 + arm_length, body_top + 30 + arm_width),
                         (70, 70, 110), -1)
        
        # Add some shadows for depth
        for obj in hallway_objects[:5]:  # Add shadows to first few objects
            x, y = obj['x'], obj['y']
            w, h = obj['width'], obj['height']
            if 0 <= x < width and 0 <= y < height:
                shadow_offset = 5
                cv2.ellipse(frame, (x + w//2 + shadow_offset, y + h + shadow_offset),
                           (w//2, h//4), 0, 0, 360, (50, 50, 50), -1)
        
        # Write frame
        video_writer.write(frame)
        
        if (frame_num + 1) % 10 == 0:
            print(f"Progress: {frame_num + 1}/{num_frames} frames ({100*(frame_num+1)/num_frames:.1f}%)", end='\r')
    
    video_writer.release()
    print(f"\nVideo created successfully: {output_path}")
    print(f"Resolution: {width}x{height}, Duration: {duration_seconds}s, FPS: {fps}")


def main():
    """Main function to generate the video."""
    output_filename = "seniorClutteredHallway.mp4"
    
    print("=" * 60)
    print("Senior Cluttered Hallway Video Generator")
    print("=" * 60)
    print()
    print("Generating video with:")
    print("  - Senior individual walking")
    print("  - Very cluttered hallway (more objects than messyPath.mp4)")
    print("  - Similar style to existing videos")
    print()
    
    # Use the advanced method for better results
    generate_video_advanced(
        output_path=output_filename,
        duration_seconds=4.0,  # 4 second video
        fps=30,
        width=1920,
        height=1080
    )
    
    print()
    print("=" * 60)
    print(f"Video generation complete!")
    print(f"Output file: {output_filename}")
    print("=" * 60)


if __name__ == "__main__":
    main()




