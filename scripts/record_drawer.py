#!/usr/bin/env python3
"""
Record video of drawer for inventory monitoring
Saves with timestamp: drawer_YYYYMMDD_HHMMSS.mp4
"""
import cv2
from datetime import datetime
import argparse
from pathlib import Path

def record_drawer_video(duration=30, output_dir='data/videos', drawer_id='drawer'):
    """Record video from webcam with timestamp"""
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{drawer_id}_{timestamp}.mp4"
    output_path = Path(output_dir) / filename
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Get actual properties
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    print(f"🎥 Recording: {filename}")
    print(f"⏱️  Duration: {duration} seconds")
    print(f"📁 Saving to: {output_path}")
    print("\nTips:")
    print("  - Keep camera steady")
    print("  - Ensure good lighting")
    print("  - Frame the entire drawer in view")
    print("  - Avoid shadows")
    print("\nPress 'q' to stop early\n")
    
    frame_count = 0
    max_frames = duration * fps
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            print("Error reading frame")
            break
        
        # Add recording indicator
        cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
        cv2.putText(frame, "REC", (50, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Show remaining time
        remaining = int((max_frames - frame_count) / fps)
        time_text = f"Time: {remaining}s"
        cv2.putText(frame, time_text, (width-150, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show timestamp
        timestamp_text = datetime.now().strftime('%H:%M:%S')
        cv2.putText(frame, timestamp_text, (width-150, height-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        out.write(frame)
        cv2.imshow('Recording Drawer', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n⏹️  Recording stopped by user")
            break
        
        frame_count += 1
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    actual_duration = frame_count / fps
    print(f"\n✅ Recording complete!")
    print(f"📊 Frames: {frame_count}")
    print(f"⏱️  Duration: {actual_duration:.1f}s")
    print(f"💾 File: {output_path}")
    print(f"📦 Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Record drawer video for inventory monitoring')
    parser.add_argument('--duration', type=int, default=30, help='Recording duration in seconds')
    parser.add_argument('--drawer-id', type=str, default='drawer', help='Drawer identifier')
    parser.add_argument('--output-dir', type=str, default='data/videos', help='Output directory')
    
    args = parser.parse_args()
    
    record_drawer_video(
        duration=args.duration,
        output_dir=args.output_dir,
        drawer_id=args.drawer_id
    )
