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
