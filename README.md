# Inventory Monitoring System

Automated inventory monitoring for drawer partitions using computer vision and HuggingFace models.

## What This Actually Automates: 2-Bin Kanban

This system exists to automate a **2-bin kanban** replenishment process: each
part type lives in two bins, one is drawn from while the other sits in
reserve, and when a bin runs empty that's the trigger to refill/reorder it
and swap it back in. The thing that needs automating isn't a precise parts
count — it's a **full / getting low / empty** state per bin, so a swap can
happen before a line runs dry. That framing drove the detection-method
decisions below: exact counts matter far less here than reliably catching
"empty."

## Features

- 🎥 Video-based monitoring with timestamp tracking
- 🤖 HuggingFace AI models for part detection
- 📧 Email alerts for low inventory
- 📊 Daily reports with charts and trends
- 🗄️ SQLite database for historical tracking
- ⏰ Timeline-based analysis
- 🌐 Streamlit web interface for easy video upload and management

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

Run the setup wizard to draw and label each partition on your test video —
it writes the ROI coordinates straight into `config/config.yaml`:

```bash
python main.py --setup
```

(Or edit `config/config.yaml` by hand and adjust ROI coordinates yourself.)

### 4. Run Detection

**Option A: Using Streamlit Web Interface (Recommended)**

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501` and:
- Upload videos through the web interface
- View statistics and processed videos
- Monitor inventory status

**Option B: Using Command Line**

```bash
python main.py
```

### 5. View Reports

Reports are saved to `data/outputs/reports/`

## Video File Naming Convention

Use this pattern: `{drawer_id}_{YYYYMMDD}_{HHMMSS}.{mp4|mov}`

Examples:
- `partition_1_20250126_143022.mp4`
- `section_a_20250126_143045.mov`

## Detection Methods: OWL-ViT vs. Edge-Density

Each drawer picks one of two detection methods via `detection_method` in
`config/config.yaml` (set interactively by `python main.py --setup`), and
different drawers in the same install can use different methods:

- **`owlvit`** — open-vocabulary object counting (HuggingFace's OWL-ViT).
  Counts individual items against `min_threshold`/`critical_threshold`.
  Works well when items are large/distinguishable enough for a detector to
  resolve them one by one.
- **`edge_density`** — Canny edge density in the drawer's ROI, compared to
  a "full" reference captured during setup. Classifies the drawer as
  OK / LOW / CRITICAL against `low_ratio` (default `0.5`) /
  `critical_ratio` (default `0.15`) — a coarse full/getting-low/empty
  state, not a smooth percentage.

**Why both exist**: testing against a real drawer of loose nails found that
OWL-ViT's detection confidence never reliably crosses a usable threshold
for a dense pile of small, near-identical parts — it reads 0 items all day
regardless of actual content. Edge density doesn't try to count individual
parts at all; a deep pile of overlapping metal has visibly more edge/glare
complexity than a thin layer even at similar coverage, so it tracks pile
*depth* well enough to reliably tell full from empty — which is exactly
the "is it time to swap the bin" signal the 2-bin kanban use case needs.
It was validated against real, precisely measured 100%/50%/0% depletion
before being wired in (see `BACKLOG.md` for the full numeric history).

Two things that matter a lot when setting up an `edge_density` drawer:
1. **The camera must be physically fixed** between recordings (tape,
   mount, bracket — anything that stops it moving). Even small drift
   silently corrupts every reading, since the ROI is a fixed pixel box.
2. **Draw the ROI box inside the compartment walls, not touching them.**
   The rigid divider walls have their own reflective edges regardless of
   contents, which creates a constant noise floor and compresses the
   readable range if included.

## Configuration

See `config/config.yaml` for all settings:
- Drawer ROI coordinates and detection method (`owlvit` or `edge_density`)
- Alert thresholds
- Email recipients
- Report schedule

## Directory Structure

```
inventory-monitor/
├── app.py             # Streamlit web interface
├── main.py            # Main CLI application
├── setup.py           # Package setup script
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

### Web Interface (Streamlit)

Launch the web interface:
```bash
streamlit run app.py
```

Features:
- **Upload Video**: Upload videos directly through the browser
- **Process Videos**: View and process queued videos
- **View Statistics**: See processed video counts, alerts, and inventory snapshots
- **Settings**: View current configuration

### Command Line

#### Record New Video
```bash
python scripts/record_drawer.py
```

#### Process Single Video
```bash
python main.py --video data/videos/drawer_20250126_140000.mp4
```

#### Process All Videos
```bash
python main.py --process-all
```

#### Generate Report
```bash
python main.py --generate-report
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

## Vision: Multi-Site Rollout

This is currently a single-installation tool (one `config.yaml`, one local
database), validated against a test drawer. The intended trajectory is
broader than that: multiple separate factory/warehouse installations, each
with its own camera(s), drawers, and local admin, plus a central
**super-admin** view across all of them — an admin panel to onboard a new
site (camera setup, draw ROI boxes, pick a detection method per drawer,
capture calibration states), a per-installation admin email for that
site's alerts, and one place to see status across every site at once.
None of that multi-site/admin-panel infrastructure is built yet — today's
architecture is intentionally single-site — but new architectural
decisions should keep this direction in mind rather than assume there will
only ever be one installation.

## Next Steps

- [ ] Record test videos of your drawer
- [ ] Run `python main.py --setup` to draw and label partitions
- [ ] Test email alerts
- [ ] Set up daily report schedule
- [ ] Fine-tune detection thresholds

## Support

For issues or questions, check the logs in `logs/inventory_monitor.log`
