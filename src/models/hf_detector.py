"""HuggingFace model detector for object detection"""
import torch
from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image
import numpy as np
import cv2


class HuggingFaceDetector:
    def __init__(self, model_name="facebook/detr-resnet-50", device="cpu"):
        self.model_name = model_name
        self.device = device
        
        print(f"Loading model: {model_name}")
        
        # Load processor and model
        self.processor = DetrImageProcessor.from_pretrained(model_name)
        self.model = DetrForObjectDetection.from_pretrained(model_name)
        self.model.to(device)
        self.model.eval()
        
        print(f"Model loaded on {device}")
    
    def detect(self, frame, confidence_threshold=0.6, text_queries=None):
        """
        Detect objects in frame
        
        Args:
            frame: numpy array (BGR format from OpenCV)
            confidence_threshold: minimum confidence for detection
            text_queries: list of text queries (for open-vocabulary models)
        
        Returns:
            list of detection dicts with keys: bbox, confidence, label
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        # Process image
        inputs = self.processor(images=pil_image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Post-process
        results = self.processor.post_process_object_detection(
            outputs,
            target_sizes=torch.tensor([pil_image.size[::-1]]).to(self.device),
            threshold=confidence_threshold
        )
        
        # Format results
        detections = []
        for result in results:
            boxes = result['boxes'].cpu().numpy()
            scores = result['scores'].cpu().numpy()
            labels = result['labels'].cpu().numpy()
            
            for box, score, label in zip(boxes, scores, labels):
                # Convert to [x1, y1, x2, y2, confidence, label]
                detection = {
                    'bbox': [int(b) for b in box],
                    'confidence': float(score),
                    'label': self.model.config.id2label[label],
                    'class_id': int(label)
                }
                detections.append(detection)
        
        return detections
