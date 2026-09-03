#!/usr/bin/env python3
"""
Inventory Monitoring System - Main Application
Processes timestamped videos, tracks inventory, sends alerts
"""

import cv2
import yaml
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from tqdm import tqdm
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.video_loader import VideoLoader
from src.models.hf_detector import HuggingFaceDetector
from src.core.monitor import InventoryMonitor
from src.utils.database import init_database, VideoRecord, InventorySnapshot, Alert
from src.alerts.email_alerts import EmailAlertSystem
from src.reports.daily_report import DailyReportGenerator

# Setup logging
def setup_logging(config):
    log_config = config.get('logging', {})
    log_file = log_config.get('file', 'logs/inventory_monitor.log')
    
    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_video_timestamp(filename):
    """
    Extract timestamp from video filename
    Expected format: drawer_YYYYMMDD_HHMMSS.mp4
    """
    try:
        # Remove extension
        name = Path(filename).stem
        
        # Split by underscore
        parts = name.split('_')
        
        if len(parts) >= 3:
            # Last two parts should be date and time
            date_str = parts[-2]
            time_str = parts[-1]
            
            # Parse timestamp
            timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return timestamp
        else:
            # Fallback to file modification time
            return datetime.fromtimestamp(Path(filename).stat().st_mtime)
    except Exception as e:
        logging.warning(f"Could not parse timestamp from {filename}: {e}")
        return datetime.fromtimestamp(Path(filename).stat().st_mtime)

def get_videos_to_process(config):
    """Get list of videos to process, sorted by timestamp"""
    watch_dir = Path(config['video']['watch_directory'])
    pattern = config['video'].get('filename_pattern', '*_*.*')
    extensions = {ext.lower().lstrip('.') for ext in config['video'].get('video_extensions', ['mp4'])}

    videos = []
    for video_path in watch_dir.glob(pattern):
        if video_path.is_file() and video_path.suffix.lower().lstrip('.') in extensions:
            timestamp = parse_video_timestamp(video_path.name)
            
            # Check if video is too old
            max_age_hours = config['video'].get('max_video_age_hours', 24)
            if max_age_hours > 0:
                age = datetime.now() - timestamp
                if age > timedelta(hours=max_age_hours):
                    logging.info(f"Skipping old video: {video_path.name} (age: {age})")
                    continue
            
            videos.append({
                'path': video_path,
                'timestamp': timestamp,
                'name': video_path.name
            })
    
    # Sort by timestamp
    videos.sort(key=lambda x: x['timestamp'])
    
    return videos

def process_video_file(video_info, config, detector, monitor, db_session, alert_system, logger):
    """Process a single video file"""
    
    video_path = video_info['path']
    timestamp = video_info['timestamp']
    
    logger.info("="*70)
    logger.info(f"Processing: {video_path.name}")
    logger.info(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    try:
        # Load video
        video = VideoLoader(str(video_path))
        
        # Create database record
        video_record = VideoRecord(
            filename=video_path.name,
            timestamp=timestamp,
            duration_seconds=video.duration,
            frames_processed=0
        )
        db_session.add(video_record)
        db_session.commit()

        # Reject videos whose frame size doesn't match what the drawer ROIs
        # were drawn against (e.g. a different camera orientation) — applying
        # those ROI coordinates to a mismatched frame silently measures the
        # wrong region.
        expected_size = config['video'].get('roi_frame_size')
        if expected_size and [video.width, video.height] != list(expected_size):
            logger.error(
                f"Skipping {video_path.name}: frame size {video.width}x{video.height} "
                f"doesn't match the size partitions were drawn at ({expected_size[0]}x{expected_size[1]}). "
                f"Re-run 'python main.py --setup' on this video, or re-record with the camera in the same orientation."
            )
            video_record.success = False
            db_session.commit()
            video.release()
            return False

        # Setup output video if enabled
        output_path = None
        out = None
        if config['video'].get('save_annotated_video'):
            output_dir = Path(config['video']['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_name = f"annotated_{video_path.stem}.mp4"
            output_path = output_dir / output_name
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                str(output_path),
                fourcc,
                video.fps,
                (video.width, video.height)
            )
            logger.info(f"Saving annotated video to: {output_path}")
        
        # Process video
        skip_frames = config['video'].get('skip_frames', 5)
        confidence = config['model'].get('confidence_threshold', 0.6)
        text_queries = config['model'].get('text_queries')
        
        frame_count = 0
        last_alert_time = {}  # Track last alert time per drawer
        alert_cooldown = timedelta(minutes=config['alerts'].get('cooldown_minutes', 60))
        
        for frame in tqdm(video.frames(skip_frames=skip_frames), 
                         total=video.frame_count//(skip_frames+1),
                         desc="Processing frames"):
            
            # Detect objects
            detections = detector.detect(
                frame,
                confidence_threshold=confidence,
                text_queries=text_queries
            )
            
            # Calculate frame timestamp
            frame_timestamp = timestamp + timedelta(seconds=frame_count/video.fps)
            
            # Analyze inventory
            results = monitor.analyze_frame(frame, detections, frame_count)
            
            # Save snapshots to database
            for drawer_id, result in results.items():
                snapshot = InventorySnapshot(
                    video_id=video_record.id,
                    drawer_id=drawer_id,
                    timestamp=frame_timestamp,
                    part_count=result['count'],
                    confidence=sum(d['confidence'] for d in result['detections']) / max(len(result['detections']), 1),
                    status=result['status']
                )
                db_session.add(snapshot)
                
                # Check if alert needed
                if result['status'] in ['LOW', 'CRITICAL']:
                    drawer_config = config['drawers'][drawer_id]
                    
                    # Check cooldown
                    should_alert = True
                    if drawer_id in last_alert_time:
                        time_since_last = frame_timestamp - last_alert_time[drawer_id]
                        if time_since_last < alert_cooldown:
                            should_alert = False
                    
                    if should_alert:
                        # Create alert record
                        alert = Alert(
                            drawer_id=drawer_id,
                            alert_type=result['status'],
                            part_count=result['count'],
                            threshold=result['threshold'],
                            created_at=frame_timestamp
                        )
                        db_session.add(alert)
                        
                        # Send email alert if enabled
                        if config['alerts'].get('enabled') and alert_system:
                            # Save frame snapshot
                            frame_output_dir = Path('data/outputs/frames')
                            frame_output_dir.mkdir(parents=True, exist_ok=True)
                            frame_path = frame_output_dir / f"alert_{drawer_id}_{frame_timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                            
                            annotated_frame = monitor.draw_results(frame.copy(), {drawer_id: result})
                            cv2.imwrite(str(frame_path), annotated_frame)
                            
                            # Send alert
                            alert_data = {
                                'title': f"Low Inventory Alert - {drawer_config['name']}",
                                'drawer_name': drawer_config['name'],
                                'current_count': result['count'],
                                'threshold': result['threshold'],
                                'timestamp': frame_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'priority': 'high' if result['status'] == 'CRITICAL' else 'medium',
                                'image_path': str(frame_path)
                            }
                            
                            try:
                                alert_system.send_alert(alert_data)
                                alert.sent_at = datetime.now()
                                logger.warning(f"Alert sent for {drawer_id}: {result['count']} parts (threshold: {result['threshold']})")
                            except Exception as e:
                                logger.error(f"Failed to send alert: {e}")
                        
                        last_alert_time[drawer_id] = frame_timestamp
            
            # Commit batch of snapshots
            if frame_count % 100 == 0:
                db_session.commit()
            
            # Draw results
            annotated_frame = monitor.draw_results(frame, results)
            
            # Add timestamp overlay
            cv2.putText(annotated_frame, 
                       frame_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                       (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.7,
                       (255, 255, 255),
                       2)
            
            # Save to output video
            if out:
                out.write(annotated_frame)
            
            # Display if enabled
            if config['processing'].get('display_video'):
                cv2.imshow('Inventory Monitor', annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Stopped by user")
                    break
            
            frame_count += 1
        
        # Update video record
        video_record.frames_processed = frame_count
        video_record.success = True
        db_session.commit()
        
        # Cleanup
        video.release()
        if out:
            out.release()
        cv2.destroyAllWindows()
        
        logger.info(f"✓ Processed {frame_count} frames")
        
        # Archive video if enabled
        if config['video'].get('archive_processed'):
            archive_dir = Path(config['video']['archive_directory'])
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            archive_path = archive_dir / video_path.name
            video_path.rename(archive_path)
            logger.info(f"✓ Archived to: {archive_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        video_record.success = False
        db_session.commit()
        return False

def check_nightly_depletion(config, db_session, alert_system, logger):
    """
    Compare each drawer's first vs. last recorded count across a processed
    batch of videos, and alert if it has fallen below alerts.depletion_threshold
    (default 50%) of its initial amount.
    """
    depletion_threshold = config['alerts'].get('depletion_threshold', 0.5)
    drawers = config.get('drawers', {})

    for drawer_id, drawer_config in drawers.items():
        first_snapshot = (
            db_session.query(InventorySnapshot)
            .filter(InventorySnapshot.drawer_id == drawer_id)
            .order_by(InventorySnapshot.timestamp.asc())
            .first()
        )
        last_snapshot = (
            db_session.query(InventorySnapshot)
            .filter(InventorySnapshot.drawer_id == drawer_id)
            .order_by(InventorySnapshot.timestamp.desc())
            .first()
        )

        if not first_snapshot or not last_snapshot or first_snapshot.id == last_snapshot.id:
            continue

        initial_count = first_snapshot.part_count
        final_count = last_snapshot.part_count
        if initial_count <= 0:
            continue

        ratio = final_count / initial_count
        if ratio >= depletion_threshold:
            continue

        logger.warning(
            f"NIGHTLY DEPLETION ALERT: {drawer_id} dropped to {final_count}/{initial_count} "
            f"({ratio:.0%}) — below {depletion_threshold:.0%} threshold"
        )

        alert = Alert(
            drawer_id=drawer_id,
            alert_type='DEPLETION',
            part_count=final_count,
            threshold=int(initial_count * depletion_threshold),
            created_at=last_snapshot.timestamp
        )
        db_session.add(alert)

        if config['alerts'].get('enabled') and alert_system:
            drawer_name = drawer_config.get('name', drawer_id)
            alert_data = {
                'title': f"Nightly Depletion Alert - {drawer_name}",
                'drawer_name': drawer_name,
                'current_count': final_count,
                'threshold': int(initial_count * depletion_threshold),
                'timestamp': last_snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'priority': 'high',
                'image_path': None
            }
            try:
                alert_system.send_alert(alert_data)
                alert.sent_at = datetime.now()
                logger.warning(f"Depletion alert emailed for {drawer_id}")
            except Exception as e:
                logger.error(f"Failed to send depletion alert email: {e}")

    db_session.commit()

def main():
    parser = argparse.ArgumentParser(description='Inventory Monitoring System')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--video', help='Process specific video file')
    parser.add_argument('--process-all', action='store_true', help='Process all videos in watch directory')
    parser.add_argument('--generate-report', action='store_true', help='Generate inventory trend report')
    parser.add_argument('--days', type=int, default=5, help='Number of days to include in the report (default: 5)')
    parser.add_argument('--setup', action='store_true', help='Draw and label partitions on a video, then update config.yaml')
    parser.add_argument('--frame', type=int, help='With --setup: frame number to draw on (skips the interactive frame picker)')

    args = parser.parse_args()

    if args.setup:
        import subprocess
        setup_cmd = [sys.executable, str(Path(__file__).parent / 'scripts' / 'find_roi.py'), '--config', args.config]
        if args.video:
            setup_cmd.append(args.video)
        if args.frame is not None:
            setup_cmd += ['--frame', str(args.frame)]
        sys.exit(subprocess.run(setup_cmd).returncode)

    # Load configuration
    with open(args.config) as f:
        config = yaml.safe_load(f)
    
    logger = setup_logging(config)
    
    logger.info("="*70)
    logger.info("INVENTORY MONITORING SYSTEM")
    logger.info("="*70)
    
    # Initialize database
    db_path = config.get('database', {}).get('path', 'data/inventory_tracking.db')
    engine, Session = init_database(db_path)
    db_session = Session()
    
    # Initialize components
    detector = None
    monitor = None
    alert_system = None
    
    if not args.generate_report:
        logger.info(f"Loading model: {config['model']['name']}")
        detector = HuggingFaceDetector(
            model_name=config['model']['name'],
            device=config['model'].get('device', 'cpu')
        )
        
        monitor = InventoryMonitor(args.config)
        
        # Initialize alert system
        if config['alerts'].get('enabled'):
            try:
                alert_system = EmailAlertSystem(config)
                logger.info("Email alert system initialized")
            except Exception as e:
                logger.warning(f"Could not initialize email alerts: {e}")
                alert_system = None
    
    try:
        if args.generate_report:
            logger.info(f"Generating {args.days}-day inventory trend report...")
            report_gen = DailyReportGenerator(config, db_session)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            report_path = report_gen.generate_report(start_date=start_date, end_date=end_date)
            logger.info(f"Report saved to: {report_path}")
            
        elif args.video:
            # Process specific video
            video_info = {
                'path': Path(args.video),
                'timestamp': parse_video_timestamp(args.video),
                'name': Path(args.video).name
            }
            process_video_file(video_info, config, detector, monitor, db_session, alert_system, logger)
            
        else:
            # Process all videos in watch directory
            videos = get_videos_to_process(config)
            
            if not videos:
                logger.info("No videos to process")
                logger.info(f"Place videos in: {config['video']['watch_directory']}")
                logger.info(f"Format: drawer_YYYYMMDD_HHMMSS.mp4 (or .mov)")
            else:
                logger.info(f"Found {len(videos)} videos to process")
                
                for video_info in videos:
                    success = process_video_file(
                        video_info, config, detector, monitor, 
                        db_session, alert_system, logger
                    )
                    
                    if not success:
                        logger.error(f"Failed to process: {video_info['name']}")

                logger.info("Checking end-of-night depletion...")
                check_nightly_depletion(config, db_session, alert_system, logger)

    except KeyboardInterrupt:
        logger.info("\nStopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        db_session.close()
        logger.info("="*70)
        logger.info("Shutdown complete")
        logger.info("="*70)

if __name__ == "__main__":
    main()
