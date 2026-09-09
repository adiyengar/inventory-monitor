"""Inventory Monitor - analyzes frames and tracks drawer inventory"""
import cv2
import yaml
import numpy as np
from pathlib import Path

from .edge_density import edge_density


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
            method = drawer_config.get('detection_method', 'owlvit')

            if method == 'edge_density':
                results[drawer_id] = self._analyze_edge_density(frame, roi, drawer_config)
            else:
                results[drawer_id] = self._analyze_owlvit(detections, roi, drawer_config)

        return results

    def _analyze_owlvit(self, detections, roi, drawer_config):
        """Count-based analysis: detections whose center falls inside the ROI."""
        parts_in_drawer = self._filter_detections_in_roi(detections, roi)
        part_count = len(parts_in_drawer)

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

        return {
            'count': part_count,
            'status': status,
            'threshold': threshold,
            'detections': parts_in_drawer,
            'roi': roi
        }

    def _analyze_edge_density(self, frame, roi, drawer_config):
        """
        State-based analysis for dense small parts OWL-ViT can't count
        individually: Canny edge density in the ROI vs. a reference value
        captured (via scripts/find_roi.py --setup) when the drawer was full.

        Not a smooth percentage gauge (validated 2026-09-10) — a coarse
        full/low/empty state detector, matching the 2-bin kanban use case.
        """
        x1, y1, x2, y2 = roi
        gray_crop = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        density = edge_density(gray_crop)

        reference = drawer_config.get('edge_density_full_reference')
        low_ratio = drawer_config.get('low_ratio', 0.5)
        critical_ratio = drawer_config.get('critical_ratio', 0.15)

        if not reference:
            # No calibration captured yet — can't determine state.
            ratio = None
            status = 'OK'
        else:
            ratio = density / reference
            if ratio < critical_ratio:
                status = 'CRITICAL'
            elif ratio < low_ratio:
                status = 'LOW'
            else:
                status = 'OK'

        pseudo_count = round(ratio * 100) if ratio is not None else 0

        return {
            'count': pseudo_count,
            'status': status,
            'threshold': round(low_ratio * 100),
            'detections': [],
            'roi': roi,
            'metric': 'edge_density',
            'ratio': ratio
        }
    
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
            unit = "%" if result.get('metric') == 'edge_density' else ""
            label = f"{drawer_id}: {count}{unit}"
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
