# YOLO

## Requirements
- Minimum Python version: Python 3.8
- Install required python packages: ```pip install -r requirements.txt```

## Running YOLO
### Folder of images as input
- Set variables in ```run_yolo_image_batch.py```
  - TEST_IMAGES_DIR should to point to the folder of input images (some test images have been provided in the ```test_image_inputs``` folder)
  - SAVE_DIR should point to the folder where you want the model output to be stored
  - MODEL_PATH should point to the YOLO model you want to use (refer to the Other information section to find the path to the latest model)
- Run ```python run_yolo_image_batch.py```

### Single image as input
- Set variables in ```run_yolo_image.py```
  - TEST_IMAGE_PATH should point to the input image
  - MODEL_PATH should point to the YOLO model you want to use
  - SAVE_DIR should point to the folder where you want the model output to be stored
- Run ```python run_yolo_image.py```

### Video stream from webcam as input
- Set variables in ```run_yolo_webcam.py```
  - MODEL_PATH should point to the YOLO model you want to use
- Run ```python run_yolo_webcam.py```

## Other Information
- Path to latest trained YOLO model: ```Phase2---AI-Chatbot-and-Hazard-Detection-Model\static_hazard_detection_model\training\runs\detect\stage2_finetune_all2```
- Path to latest training data: ```Phase2---AI-Chatbot-and-Hazard-Detection-Model\static_hazard_detection_model\training\final_fall_hazard_dataset_jan5```
- Path to training script: ```Phase2---AI-Chatbot-and-Hazard-Detection-Model\static_hazard_detection_model\training\train_yolo_2stage.py```

---
# SAM3