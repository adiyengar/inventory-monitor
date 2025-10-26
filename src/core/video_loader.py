"""Video loader for processing video files"""
import cv2
from pathlib import Path


class VideoLoader:
    def __init__(self, video_path):
        self.video_path = Path(video_path)
        self.cap = cv2.VideoCapture(str(self.video_path))
        
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate duration
        if self.fps > 0:
            self.duration = self.frame_count / self.fps
        else:
            self.duration = 0
        
        self.current_frame = 0
    
    def frames(self, skip_frames=0):
        """Generator that yields video frames"""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Skip frames if needed
            if skip_frames > 0 and frame_idx % (skip_frames + 1) != 0:
                frame_idx += 1
                continue
            
            yield frame
            frame_idx += 1
            self.current_frame = frame_idx
    
    def release(self):
        """Release video capture"""
        if self.cap is not None:
            self.cap.release()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.release()
