"""HuggingFace model detector for object detection.

Supports two model types:
  - DETR (facebook/detr-resnet-50): fixed COCO vocabulary, no text queries
  - OWL-ViT (google/owlvit-base-patch32): open-vocabulary, uses text_queries
"""
import torch
from PIL import Image
import numpy as np
import cv2


class HuggingFaceDetector:
    def __init__(self, model_name="google/owlvit-base-patch32", device="cpu"):
        self.model_name = model_name
        self.device = device
        self._is_owlvit = "owlvit" in model_name.lower() or "owl" in model_name.lower()

        print(f"Loading model: {model_name}")

        if self._is_owlvit:
            from transformers import OwlViTProcessor, OwlViTForObjectDetection
            self.processor = OwlViTProcessor.from_pretrained(model_name)
            self.model = OwlViTForObjectDetection.from_pretrained(model_name)
        else:
            from transformers import DetrImageProcessor, DetrForObjectDetection
            self.processor = DetrImageProcessor.from_pretrained(model_name)
            self.model = DetrForObjectDetection.from_pretrained(model_name)

        self.model.to(device)
        self.model.eval()
        print(f"Model loaded on {device}")

    def detect(self, frame, confidence_threshold=0.1, text_queries=None):
        """
        Detect objects in frame.

        Args:
            frame: numpy array (BGR format from OpenCV)
            confidence_threshold: minimum confidence score
            text_queries: list of strings e.g. ["screw", "coin"] — required for OWL-ViT

        Returns:
            list of dicts with keys: bbox, confidence, label
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)

        if self._is_owlvit:
            return self._detect_owlvit(pil_image, confidence_threshold, text_queries)
        else:
            return self._detect_detr(pil_image, confidence_threshold)

    def _detect_owlvit(self, pil_image, confidence_threshold, text_queries):
        if not text_queries:
            raise ValueError("text_queries must be provided for OWL-ViT")

        # Processor expects a list-of-lists: one query list per image
        inputs = self.processor(
            text=[text_queries],
            images=pil_image,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        target_sizes = torch.tensor([pil_image.size[::-1]]).to(self.device)
        results = self.processor.post_process_object_detection(
            outputs=outputs,
            threshold=confidence_threshold,
            target_sizes=target_sizes
        )[0]

        detections = []
        boxes = results["boxes"].cpu().numpy()
        scores = results["scores"].cpu().numpy()
        labels = results["labels"].cpu().numpy()

        for box, score, label_idx in zip(boxes, scores, labels):
            detections.append({
                "bbox": [int(b) for b in box],
                "confidence": float(score),
                "label": text_queries[label_idx],
                "class_id": int(label_idx)
            })

        return detections

    def _detect_detr(self, pil_image, confidence_threshold):
        inputs = self.processor(images=pil_image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        results = self.processor.post_process_object_detection(
            outputs,
            target_sizes=torch.tensor([pil_image.size[::-1]]).to(self.device),
            threshold=confidence_threshold
        )

        detections = []
        for result in results:
            boxes = result["boxes"].cpu().numpy()
            scores = result["scores"].cpu().numpy()
            labels = result["labels"].cpu().numpy()

            for box, score, label in zip(boxes, scores, labels):
                detections.append({
                    "bbox": [int(b) for b in box],
                    "confidence": float(score),
                    "label": self.model.config.id2label[label],
                    "class_id": int(label)
                })

        return detections
