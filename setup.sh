#!/bin/bash
# Complete Project Setup for Inventory Monitoring System
# Run this script to create all directories and initial files

echo "🚀 Setting up Inventory Monitoring System..."
echo "=============================================="

# Create directory structure
echo "📁 Creating directories..."
mkdir -p src/{core,models,utils,alerts,reports}
mkdir -p data/{videos,processed,outputs/{frames,reports,videos}}
mkdir -p config
mkdir -p tests
mkdir -p scripts
mkdir -p logs
mkdir -p templates/{email,reports}

# Create __init__.py files
echo "📝 Creating Python package files..."
touch src/__init__.py
touch src/core/__init__.py
touch src/models/__init__.py
touch src/utils/__init__.py
touch src/alerts/__init__.py
touch src/reports/__init__.py

# Create .gitkeep files for empty directories
touch data/videos/.gitkeep
touch data/processed/.gitkeep
touch data/outputs/frames/.gitkeep
touch data/outputs/reports/.gitkeep
touch data/outputs/videos/.gitkeep
touch logs/.gitkeep

# Create .gitignore
echo "🔒 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
*.egg-info/
.eggs/
build/
dist/

# Virtual Environment
venv/
env/

# IDE
.vscode/
.idea/
*.swp
.DS_Store
.cursor/

# Data & Videos
data/videos/*.mp4
data/videos/*.avi
data/videos/*.mov
data/processed/*
data/outputs/*
!data/videos/.gitkeep
!data/processed/.gitkeep
!data/outputs/.gitkeep

# Models
models/
.cache/
*.pt
*.pth

# Sensitive
.env
config/secrets.yaml
*.log

# Logs
logs/*.log

# Reports
data/outputs/reports/*.html
data/outputs/reports/*.pdf

# macOS
.DS_Store
.AppleDouble
._*
EOF

# Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
# Core ML & CV
opencv-python==4.8.1.78
numpy==1.24.3
pillow==10.0.0
torch==2.1.0
torchvision==0.16.0
transformers==4.35.0

# Video processing
imageio==2.31.5
imageio-ffmpeg==0.4.9

# Utilities
pyyaml==6.0.1
python-dotenv==1.0.0
tqdm==4.66.1
pandas==2.0.3

# Email & Alerts
sendgrid==6.11.0
python-dateutil==2.8.2
jinja2==3.1.2

# Reports & Visualization
matplotlib==3.7.2
seaborn==0.12.2
plotly==5.17.0

# Web Dashboard (optional)
flask==3.0.0
gradio==4.7.1

# Database (for tracking)
sqlalchemy==2.0.21

# Testing
pytest==7.4.0
pytest-cov==4.1.0
EOF

# Create .env template
echo "🔐 Creating .env template..."
cat > .env.example << 'EOF'
# Email Configuration (SendGrid)
SENDGRID_API_KEY=your_sendgrid_api_key_here
ALERT_EMAIL_FROM=inventory@yourcompany.com
ALERT_EMAIL_TO=manager@yourcompany.com,supervisor@yourcompany.com

# Or use SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password

# Alert Thresholds
CRITICAL_THRESHOLD=10
WARNING_THRESHOLD=20

# Report Schedule
DAILY_REPORT_TIME=08:00
REPORT_RECIPIENTS=team@yourcompany.com

# Video Processing
VIDEO_RETENTION_DAYS=7
PROCESS_INTERVAL_HOURS=1
EOF

# Create main configuration
echo "⚙️ Creating config files..."
cat > config/config.yaml << 'EOF'
# Main Configuration File
project:
  name: "Inventory Monitoring System"
  version: "1.0.0"
  timezone: "America/Chicago"

# Video source configuration
video:
  # Directory to watch for new videos
  watch_directory: "data/videos"
  # Video file naming convention: drawer_YYYYMMDD_HHMMSS.mp4
  filename_pattern: "*_*.mp4"
  # Process videos in chronological order
  process_order: "timestamp"
  # Archive processed videos
  archive_processed: true
  archive_directory: "data/processed"
  # Output settings
  save_annotated_video: true
  output_directory: "data/outputs/videos"
  # Processing
  skip_frames: 5  # Process every 5th frame for speed
  max_video_age_hours: 24  # Ignore videos older than 24 hours

# HuggingFace model configuration
model:
  name: "facebook/detr-resnet-50"
  # Alternative models:
  # "hustvl/yolos-tiny" - faster
  # "google/owlvit-base-patch32" - text-based detection
  confidence_threshold: 0.6
  device: "cpu"  # or "cuda" if you have GPU
  
  # For open-vocabulary models (OWL-ViT)
  text_queries:
    - "screw"
    - "bolt"
    - "nut"
    - "washer"
    - "small part"
    - "fastener"

# Drawer/partition definitions
# Adjust coordinates after recording your first video
drawers:
  partition_1:
    name: "Section A - Screws"
    roi: [50, 50, 400, 350]  # [x1, y1, x2, y2] in pixels
    min_threshold: 15
    critical_threshold: 5
    part_type: "M8 screws"
    
  partition_2:
    name: "Section B - Bolts"
    roi: [450, 50, 800, 350]
    min_threshold: 20
    critical_threshold: 8
    part_type: "M6 bolts"
    
  partition_3:
    name: "Section C - Nuts"
    roi: [850, 50, 1200, 350]
    min_threshold: 25
    critical_threshold: 10
    part_type: "Hex nuts"

# Alert configuration
alerts:
  enabled: true
  methods:
    - email
    - log
  
  # Email settings
  email:
    enabled: true
    provider: "sendgrid"  # or "smtp"
    subject_prefix: "[Inventory Alert]"
    include_images: true
    
  # Alert rules
  rules:
    critical:
      threshold_type: "below"  # below critical_threshold
      priority: "high"
      immediate_notification: true
    
    warning:
      threshold_type: "below"  # below min_threshold
      priority: "medium"
      immediate_notification: false
      
    restock_needed:
      threshold_type: "below"
      threshold_percentage: 30  # 30% of baseline
      priority: "medium"
      immediate_notification: false
  
  # Rate limiting (avoid spam)
  cooldown_minutes: 60  # Don't send same alert twice within 60 min

# Daily report configuration
reports:
  enabled: true
  schedule:
    daily: true
    time: "08:00"  # 8 AM
    weekends: false
  
  include:
    - summary_statistics
    - trend_charts
    - alert_history
    - low_stock_forecast
    - video_thumbnails
  
  format: "html"  # html, pdf, or both
  
  recipients:
    - "manager@company.com"
    - "inventory@company.com"

# Database for tracking
database:
  enabled: true
  type: "sqlite"
  path: "data/inventory_tracking.db"
  
# Logging
logging:
  level: "INFO"
  file: "logs/inventory_monitor.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
EOF

# Create database schema
echo "🗄️ Creating database schema..."
cat > src/utils/database.py << 'EOF'
"""Database models for inventory tracking"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class VideoRecord(Base):
    __tablename__ = 'video_records'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, default=datetime.now)
    duration_seconds = Column(Float)
    frames_processed = Column(Integer)
    success = Column(Boolean, default=True)

class InventorySnapshot(Base):
    __tablename__ = 'inventory_snapshots'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer)
    drawer_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    part_count = Column(Integer, nullable=False)
    confidence = Column(Float)
    status = Column(String)  # OK, WARNING, CRITICAL

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    drawer_id = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # CRITICAL, WARNING
    part_count = Column(Integer)
    threshold = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    sent_at = Column(DateTime)
    resolved_at = Column(DateTime)

def init_database(db_path='data/inventory_tracking.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)
EOF

# Create email alert system
echo "📧 Creating email alert system..."
cat > src/alerts/email_alerts.py << 'EOF'
"""Email alert system for inventory notifications"""
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import smtplib
from jinja2 import Template
from pathlib import Path

class EmailAlertSystem:
    def __init__(self, config):
        self.config = config
        self.email_config = config['alerts']['email']
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.from_email = os.getenv('ALERT_EMAIL_FROM')
        self.to_emails = os.getenv('ALERT_EMAIL_TO', '').split(',')
        
        # Load email template
        template_path = Path('templates/email/alert_template.html')
        if template_path.exists():
            with open(template_path) as f:
                self.template = Template(f.read())
        else:
            self.template = None
    
    def send_alert(self, alert_data):
        """Send immediate alert email"""
        subject = f"{self.email_config['subject_prefix']} {alert_data['title']}"
        
        if self.template:
            html_content = self.template.render(
                title=alert_data['title'],
                drawer_name=alert_data['drawer_name'],
                current_count=alert_data['current_count'],
                threshold=alert_data['threshold'],
                timestamp=alert_data['timestamp'],
                priority=alert_data['priority'],
                image_path=alert_data.get('image_path')
            )
        else:
            html_content = f"""
            <html>
            <body>
                <h2 style="color: #d32f2f;">Inventory Alert</h2>
                <p><strong>Drawer:</strong> {alert_data['drawer_name']}</p>
                <p><strong>Current Count:</strong> {alert_data['current_count']}</p>
                <p><strong>Threshold:</strong> {alert_data['threshold']}</p>
                <p><strong>Status:</strong> {alert_data['priority'].upper()}</p>
                <p><strong>Time:</strong> {alert_data['timestamp']}</p>
            </body>
            </html>
            """
        
        self._send_email(subject, html_content, alert_data.get('image_path'))
    
    def _send_email(self, subject, html_content, image_path=None):
        """Internal method to send email via SMTP"""
        try:
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Attach image if provided
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<alert_image>')
                    msg.attach(img)
            
            # Send via SMTP
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USERNAME')
            smtp_pass = os.getenv('SMTP_PASSWORD')
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            print(f"✓ Alert email sent to {', '.join(self.to_emails)}")
            
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
EOF

# Create daily report generator
echo "📊 Creating report generator..."
cat > src/reports/daily_report.py << 'EOF'
"""Daily inventory report generator"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Template
import base64
from io import BytesIO

class DailyReportGenerator:
    def __init__(self, config, db_session):
        self.config = config
        self.db_session = db_session
        
        # Load template
        template_path = Path('templates/reports/daily_report.html')
        if template_path.exists():
            with open(template_path) as f:
                self.template = Template(f.read())
    
    def generate_report(self, start_date=None, end_date=None):
        """Generate daily report with charts and statistics"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        # Query data from database
        from src.utils.database import InventorySnapshot, Alert
        
        snapshots = self.db_session.query(InventorySnapshot).filter(
            InventorySnapshot.timestamp.between(start_date, end_date)
        ).all()
        
        alerts = self.db_session.query(Alert).filter(
            Alert.created_at.between(start_date, end_date)
        ).all()
        
        # Prepare data
        df = pd.DataFrame([{
            'drawer': s.drawer_id,
            'timestamp': s.timestamp,
            'count': s.part_count,
            'status': s.status
        } for s in snapshots])
        
        # Generate statistics
        stats = self._calculate_statistics(df, alerts)
        
        # Generate charts
        charts = self._generate_charts(df)
        
        # Render HTML report
        html_content = self.template.render(
            report_date=end_date.strftime('%Y-%m-%d'),
            statistics=stats,
            charts=charts,
            alerts=alerts
        )
        
        # Save report
        output_path = Path(f"data/outputs/reports/daily_report_{end_date.strftime('%Y%m%d')}.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"✓ Report generated: {output_path}")
        return output_path
    
    def _calculate_statistics(self, df, alerts):
        """Calculate summary statistics"""
        if df.empty:
            return {}
        
        stats = {
            'total_snapshots': len(df),
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a.alert_type == 'CRITICAL']),
            'drawers_monitored': df['drawer'].nunique(),
            'avg_parts_per_drawer': df.groupby('drawer')['count'].mean().to_dict(),
            'min_counts': df.groupby('drawer')['count'].min().to_dict(),
            'max_counts': df.groupby('drawer')['count'].max().to_dict()
        }
        
        return stats
    
    def _generate_charts(self, df):
        """Generate visualization charts"""
        charts = {}
        
        if df.empty:
            return charts
        
        # Timeline chart
        fig, ax = plt.subplots(figsize=(12, 6))
        for drawer in df['drawer'].unique():
            drawer_data = df[df['drawer'] == drawer]
            ax.plot(drawer_data['timestamp'], drawer_data['count'], 
                   marker='o', label=drawer)
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Part Count')
        ax.set_title('Inventory Levels Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Convert to base64 for HTML embedding
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        charts['timeline'] = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return charts
EOF

# Create video recorder script
echo "📹 Creating video recorder script..."
cat > scripts/record_drawer.py << 'EOF'
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
EOF
chmod +x scripts/record_drawer.py

# Create email template
echo "📧 Creating email templates..."
mkdir -p templates/email
cat > templates/email/alert_template.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .alert-box { 
            border-left: 4px solid #d32f2f; 
            background: #ffebee; 
            padding: 15px; 
            margin: 20px 0; 
        }
        .alert-box.warning { border-color: #ff9800; background: #fff3e0; }
        .stats { background: #f5f5f5; padding: 15px; border-radius: 5px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚨 {{ title }}</h2>
        
        <div class="alert-box {% if priority == 'high' %}critical{% else %}warning{% endif %}">
            <h3>{{ drawer_name }}</h3>
            <p><strong>Current Count:</strong> {{ current_count }} parts</p>
            <p><strong>Threshold:</strong> {{ threshold }} parts</p>
            <p><strong>Status:</strong> {{ priority|upper }}</p>
            <p><strong>Time:</strong> {{ timestamp }}</p>
        </div>
        
        {% if image_path %}
        <div style="text-align: center; margin: 20px 0;">
            <img src="cid:alert_image" style="max-width: 100%; border: 1px solid #ddd;" />
        </div>
        {% endif %}
        
        <div class="footer">
            <p>This is an automated alert from the Inventory Monitoring System.</p>
            <p>Please check the drawer and restock if necessary.</p>
        </div>
    </div>
</body>
</html>
EOF

# Create report template
mkdir -p templates/reports
cat > templates/reports/daily_report.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Daily Inventory Report - {{ report_date }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 32px; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; font-size: 14px; margin-top: 5px; }
        .chart { margin: 30px 0; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert-list { margin: 20px 0; }
        .alert-item { background: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-item.critical { background: #ffebee; border-color: #d32f2f; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Daily Inventory Report</h1>
        <p>{{ report_date }}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ statistics.total_snapshots }}</div>
            <div class="stat-label">Total Checks</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ statistics.drawers_monitored }}</div>
            <div class="stat-label">Drawers Monitored</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ statistics.total_alerts }}</div>
            <div class="stat-label">Total Alerts</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ statistics.critical_alerts }}</div>
            <div class="stat-label">Critical Alerts</div>
        </div>
    </div>
    
    {% if charts.timeline %}
    <div class="chart">
        <h3>Inventory Levels Timeline</h3>
        <img src="data:image/png;base64,{{ charts.timeline }}" style="max-width: 100%;" />
    </div>
    {% endif %}
    
    {% if alerts %}
    <div class="alert-list">
        <h3>Recent Alerts</h3>
        {% for alert in alerts %}
        <div class="alert-item {{ 'critical' if alert.alert_type == 'CRITICAL' else '' }}">
            <strong>{{ alert.drawer_id }}</strong> - {{ alert.alert_type }}<br>
            Count: {{ alert.part_count }} / Threshold: {{ alert.threshold }}<br>
            <small>{{ alert.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</small>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
EOF

# Create README
echo "📝 Creating README..."
cat > README.md << 'EOF'
# Inventory Monitoring System

Automated inventory monitoring for drawer partitions using computer vision and HuggingFace models.

## Features

- 🎥 Video-based monitoring with timestamp tracking
- 🤖 HuggingFace AI models for part detection
- 📧 Email alerts for low inventory
- 📊 Daily reports with charts and trends
- 🗄️ SQLite database for historical tracking
- ⏰ Timeline-based analysis

## Quick Start

### 1. Setup

```bash
# Clone repository
git clone <your-repo-url>
cd inventory-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your email credentials
```

### 2. Record Test Video

```bash
# Record 30-second video of your drawer
python scripts/record_drawer.py --duration 30 --drawer-id partition_1
```

Videos are saved with timestamp: `drawer_YYYYMMDD_HHMMSS.mp4`

### 3. Configure Drawers

Edit `config/config.yaml` and adjust ROI coordinates for your drawer partitions.

### 4. Run Detection

```bash
python main.py
```

### 5. View Reports

Reports are saved to `data/outputs/reports/`

## Video File Naming Convention

Use this pattern: `{drawer_id}_{YYYYMMDD}_{HHMMSS}.mp4`

Examples:
- `partition_1_20250126_143022.mp4`
- `section_a_20250126_143045.mp4`

## Configuration

See `config/config.yaml` for all settings:
- Drawer ROI coordinates
- Alert thresholds
- Email recipients
- Report schedule

## Directory Structure

```
inventory-monitor/
├── src/
│   ├── core/          # Video processing & detection
│   ├── models/        # HuggingFace models
│   ├── alerts/        # Email alert system
│   ├── reports/       # Report generation
│   └── utils/         # Database & utilities
├── data/
│   ├── videos/        # Input videos (timestamped)
│   ├── processed/     # Archived videos
│   └── outputs/       # Reports & annotated videos
├── config/            # Configuration files
├── scripts/           # Utility scripts
├── templates/         # Email & report templates
└── logs/              # Application logs
```

## Usage

### Record New Video
```bash
python scripts/record_drawer.py
```

### Process Single Video
```bash
python main.py --video data/videos/drawer_20250126_140000.mp4
```

### Process All Videos
```bash
python main.py --process-all
```

### Generate Report
```bash
python -m src.reports.daily_report
```

## Email Setup

### Using Gmail
1. Enable 2-factor authentication
2. Create app-specific password
3. Update `.env`:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Using SendGrid
1. Get API key from sendgrid.com
2. Update `.env`:
```
SENDGRID_API_KEY=your-api-key
```

## Next Steps

- [ ] Record test videos of your drawer
- [ ] Adjust ROI coordinates in config
- [ ] Test email alerts
- [ ] Set up daily report schedule
- [ ] Fine-tune detection thresholds

## Support

For issues or questions, check the logs in `logs/inventory_monitor.log`
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📁 Project structure created"
echo "📝 Configuration files ready"
echo "🎯 Next steps:"
echo ""
echo "1. Create virtual environment:"
echo "   python3 -m venv venv && source venv/bin/activate"
echo ""
echo "2. Install dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Configure email:"
echo "   cp .env.example .env"
echo "   # Edit .env with your credentials"
echo ""
echo "4. Record test video:"
echo "   python scripts/record_drawer.py"
echo ""
echo "5. Run the system:"
echo "   python main.py"
echo ""
echo "🚀 Ready to start!"