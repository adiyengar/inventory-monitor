"""
Streamlit Frontend for Inventory Monitoring System
Upload videos and process them for inventory tracking
"""
import streamlit as st
import yaml
from pathlib import Path
from datetime import datetime
import sys
import os
import subprocess
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.database import init_database, VideoRecord, InventorySnapshot, Alert

# Page configuration
st.set_page_config(
    page_title="Inventory Monitor",
    page_icon="📦",
    layout="wide"
)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'detector' not in st.session_state:
    st.session_state.detector = None
if 'monitor' not in st.session_state:
    st.session_state.monitor = None

# Load configuration
@st.cache_data
def load_config():
    config_path = Path('config/config.yaml')
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return None

def format_video_filename(drawer_id, timestamp=None):
    """Format video filename according to convention"""
    if timestamp is None:
        timestamp = datetime.now()
    return f"{drawer_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.mp4"

def save_uploaded_video(uploaded_file, drawer_id):
    """Save uploaded video with proper naming convention"""
    config = load_config()
    if not config:
        return None, "Configuration file not found"
    
    watch_dir = Path(config['video']['watch_directory'])
    watch_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now()
    filename = format_video_filename(drawer_id, timestamp)
    file_path = watch_dir / filename
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return file_path, None
    except Exception as e:
        return None, str(e)

def get_video_stats():
    """Get statistics about processed videos"""
    config = load_config()
    if not config:
        return {}
    
    db_path = config.get('database', {}).get('path', 'data/inventory_tracking.db')
    if not Path(db_path).exists():
        return {}
    
    try:
        engine, Session = init_database(db_path)
        db_session = Session()
        
        # Get video count
        video_count = db_session.query(VideoRecord).count()
        processed_count = db_session.query(VideoRecord).filter(VideoRecord.success == True).count()
        
        # Get latest video
        latest_video = db_session.query(VideoRecord).order_by(VideoRecord.timestamp.desc()).first()
        
        # Get alert count
        alert_count = db_session.query(Alert).count()
        
        # Get latest inventory snapshots
        latest_snapshots = db_session.query(InventorySnapshot).order_by(
            InventorySnapshot.timestamp.desc()
        ).limit(10).all()
        
        db_session.close()
        
        return {
            'total_videos': video_count,
            'processed_videos': processed_count,
            'latest_video': latest_video,
            'alert_count': alert_count,
            'latest_snapshots': latest_snapshots
        }
    except Exception as e:
        st.error(f"Error loading stats: {e}")
        return {}

def main():
    config = load_config()
    if not config:
        st.error("Configuration file not found. Please ensure config/config.yaml exists.")
        return
    
    st.title("📦 Inventory Monitoring System")
    st.markdown("Upload videos to track inventory in drawer partitions")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Upload Video", "Process Videos", "View Statistics", "Settings"])
    
    if page == "Upload Video":
        st.header("Upload Video")
        st.markdown("Upload a video file to be processed for inventory tracking.")
        
        # Get drawer IDs from config
        drawers = config.get('drawers', {})
        drawer_options = {drawer_id: drawer_config.get('name', drawer_id) 
                         for drawer_id, drawer_config in drawers.items()}
        
        if not drawer_options:
            st.warning("No drawers configured. Please configure drawers in config/config.yaml")
        else:
            # Drawer selection
            selected_drawer = st.selectbox(
                "Select Drawer/Partition",
                options=list(drawer_options.keys()),
                format_func=lambda x: drawer_options[x]
            )
            
            # Video upload
            uploaded_file = st.file_uploader(
                "Choose a video file",
                type=['mp4', 'avi', 'mov', 'mkv'],
                help="Upload a video file of your drawer/partition"
            )
            
            if uploaded_file is not None:
                # Display video info
                st.info(f"**File:** {uploaded_file.name}\n\n**Size:** {uploaded_file.size / 1024 / 1024:.2f} MB")
                
                # Preview video
                if uploaded_file.type.startswith('video'):
                    st.video(uploaded_file)
                
                # Upload button
                if st.button("Upload Video", type="primary"):
                    with st.spinner("Saving video..."):
                        file_path, error = save_uploaded_video(uploaded_file, selected_drawer)
                        
                        if error:
                            st.error(f"Error saving video: {error}")
                        else:
                            st.success(f"✅ Video saved successfully!")
                            st.info(f"**Location:** `{file_path}`\n\n**Filename:** `{file_path.name}`")
                            st.markdown("---")
                            st.markdown("### Next Steps")
                            st.markdown("1. Go to **Process Videos** to analyze the uploaded video")
                            st.markdown("2. Or use the command line: `python main.py --process-all`")
    
    elif page == "Process Videos":
        st.header("Process Videos")
        st.markdown("Process uploaded videos for inventory detection and tracking.")
        
        watch_dir = Path(config['video']['watch_directory'])
        
        # List videos in watch directory
        if watch_dir.exists():
            video_files = list(watch_dir.glob("*.mp4")) + list(watch_dir.glob("*.avi")) + list(watch_dir.glob("*.mov"))
            
            if not video_files:
                st.info(f"No videos found in `{watch_dir}`. Upload videos first!")
            else:
                st.markdown(f"**Found {len(video_files)} video(s) in watch directory**")
                
                # Display video list
                for video_file in video_files:
                    with st.expander(f"📹 {video_file.name}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"Path: {video_file}")
                            st.text(f"Size: {video_file.stat().st_size / 1024 / 1024:.2f} MB")
                            st.text(f"Modified: {datetime.fromtimestamp(video_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
                        with col2:
                            if st.button("Process", key=f"process_{video_file.name}"):
                                st.session_state.processing = True
                                st.session_state.current_video = str(video_file)
                
                # Process button
                if st.button("Process All Videos", type="primary"):
                    st.session_state.processing = True
                
                # Processing status
                if st.session_state.processing:
                    st.info("Processing videos... This may take a while.")
                    st.markdown("**Note:** For better performance, use the command line: `python main.py --process-all`")
        else:
            st.warning(f"Watch directory `{watch_dir}` does not exist. Creating it...")
            watch_dir.mkdir(parents=True, exist_ok=True)
    
    elif page == "View Statistics":
        st.header("Statistics")
        st.markdown("View statistics about processed videos and inventory tracking.")
        
        stats = get_video_stats()
        
        if not stats:
            st.info("No data available yet. Process some videos first!")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Videos", stats.get('total_videos', 0))
            with col2:
                st.metric("Processed Videos", stats.get('processed_videos', 0))
            with col3:
                st.metric("Total Alerts", stats.get('alert_count', 0))
            with col4:
                success_rate = (stats.get('processed_videos', 0) / max(stats.get('total_videos', 1), 1)) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Latest video info
            if stats.get('latest_video'):
                st.markdown("### Latest Processed Video")
                latest = stats['latest_video']
                st.json({
                    "Filename": latest.filename,
                    "Timestamp": latest.timestamp.strftime('%Y-%m-%d %H:%M:%S') if latest.timestamp else None,
                    "Duration": f"{latest.duration_seconds:.2f} seconds" if latest.duration_seconds else None,
                    "Frames Processed": latest.frames_processed,
                    "Success": latest.success
                })
            
            # Latest snapshots
            if stats.get('latest_snapshots'):
                st.markdown("### Recent Inventory Snapshots")
                snapshots = stats['latest_snapshots']
                
                if snapshots:
                    snapshot_data = []
                    for snap in snapshots[:10]:
                        snapshot_data.append({
                            "Drawer ID": snap.drawer_id,
                            "Timestamp": snap.timestamp.strftime('%Y-%m-%d %H:%M:%S') if snap.timestamp else None,
                            "Part Count": snap.part_count,
                            "Status": snap.status,
                            "Confidence": f"{snap.confidence:.2f}" if snap.confidence else None
                        })
                    st.dataframe(snapshot_data, use_container_width=True)
    
    elif page == "Settings":
        st.header("Settings")
        st.markdown("View and manage system configuration.")
        
        st.markdown("### Current Configuration")
        st.json(config)
        
        st.markdown("### Directories")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Watch Directory:**")
            st.code(config['video']['watch_directory'])
            
            st.markdown("**Output Directory:**")
            st.code(config['video']['output_directory'])
        
        with col2:
            st.markdown("**Archive Directory:**")
            st.code(config['video']['archive_directory'])
            
            st.markdown("**Database Path:**")
            st.code(config['database']['path'])
        
        st.markdown("### Model Configuration")
        st.json(config['model'])
        
        st.markdown("### Drawer Configuration")
        st.json(config['drawers'])

if __name__ == "__main__":
    main()

