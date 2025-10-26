"""Inventory Monitor - analyzes frames and tracks drawer inventory"""
import cv2
import yaml
import numpy as np
from pathlib import Path


class InventoryMonitor:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.drawers = self.config.get('drawers', {})
    
    def analyze_frame(self, frame, detections, frame_number):
        """
        Analyze frame and count parts in each drawer
        
        Args:
            frame: numpy array (frame image)
            detections: list of detection dicts from detector
            frame_number: current frame number
        
        Returns:
            dict mapping drawer_id to analysis results
        """
        results = {}
        
        for drawer_id, drawer_config in self.drawers.items():
            # Get ROI coordinates
            roi = drawer_config.get('roi', [0, 0, frame.shape[1], frame.shape[0]])
            
            # Check if any detections are in the ROI
            parts_in_drawer = self._filter_detections_in_roi(detections, roi)
            
            # Count parts
            part_count = len(parts_in_drawer)
            
            # Determine status
            min_threshold = drawer_config.get('min_threshold', 20)
            critical_threshold = drawer_config.get('critical_threshold', 10)
            
            if part_count < critical_threshold:
                status = 'CRITICAL'
                threshold = critical_threshold
            elif part_count < min_threshold:
                status = 'LOW'
                threshold = min_threshold
            else:
                status = 'OK'
                threshold = min_threshold
            
            results[drawer_id] = {
                'count': part_count,
                'status': status,
                'threshold': threshold,
                'detections': parts_in_drawer,
                'roi': roi
            }
        
        return results
    
    def _filter_detections_in_roi(self, detections, roi):
        """Filter detections that fall within the ROI"""
        x1, y1, x2, y2 = roi
        filtered = []
        
        for detection in detections:
            bbox = detection['bbox']  # [x1, y1, x2, y2]
            det_x1, det_y1, det_x2, det_y2 = bbox
            
            # Check if detection center is in ROI
            center_x = (det_x1 + det_x2) / 2
            center_y = (det_y1 + det_y2) / 2
            
            if x1 <= center_x <= x2 and y1 <= center_y <= y2:
                filtered.append(detection)
        
        return filtered
    
    def draw_results(self, frame, results):
        """
        Draw results on frame with bounding boxes and labels
        
        Args:
            frame: numpy array (frame image)
            results: dict mapping drawer_id to analysis results
        
        Returns:
            annotated frame
        """
        annotated_frame = frame.copy()
        
        for drawer_id, result in results.items():
            roi = result['roi']
            count = result['count']
            status = result['status']
            
            # Draw ROI rectangle
            x1, y1, x2, y2 = roi
            color = self._get_color_for_status(status)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{drawer_id}: {count}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, 
                         (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), 
                         color, -1)
            cv2.putText(annotated_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw detections in ROI
            for detection in result['detections']:
                bbox = detection['bbox']
                confidence = detection['confidence']
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, 
                             (bbox[0], bbox[1]), 
                             (bbox[2], bbox[3]), 
                             (0, 255, 0), 2)
                
                # Draw confidence
                conf_text = f"{confidence:.2f}"
                cv2.putText(annotated_frame, conf_text, 
                           (bbox[0], bbox[1] - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        return annotated_frame
    
    def _get_color_for_status(self, status):
        """Get color for status"""
        colors = {
            'OK': (0, 255, 0),      # Green
            'LOW': (0, 165, 255),   # Orange
            'CRITICAL': (0, 0, 255) # Red
        }
        return colors.get(status, (128, 128, 128))
