# 🧪 Quick Test Guide

## Step 1: Place Your Videos

Copy your 10 video files to: `data/videos/`

Example:
```bash
cp ~/Downloads/video1.mp4 data/videos/partition_1_20250126_140000.mp4
cp ~/Downloads/video2.mp4 data/videos/partition_2_20250126_140530.mp4
# ... etc
```

## Step 2: Check Video Names

Make sure filenames match this pattern:
```
partition_1_20250126_140000.mp4
partition_2_20250126_140530.mp4
partition_3_20250126_141000.mp4
```

## Step 3: Configure Drawer ROIs

Before processing, you may need to adjust the ROI (Region of Interest) coordinates in `config/config.yaml` for each drawer section.

Look at your first video and note where the parts are located, then update the roi coordinates:
```yaml
drawers:
  partition_1:
    roi: [x1, y1, x2, y2]  # Adjust these values
```

## Step 4: Run Test

**Test with 1 video first:**
```bash
python main.py --video data/videos/partition_1_20250126_140000.mp4
```

**Process all videos:**
```bash
python main.py --process-all
```

## Step 5: Check Results

View outputs:
```bash
# Annotated videos
ls -lh data/outputs/videos/

# Alert images (if any)
ls -lh data/outputs/frames/

# Database
sqlite3 data/inventory_tracking.db "SELECT * FROM inventory_snapshots LIMIT 10;"

# Logs
tail -f logs/inventory_monitor.log
```

## Troubleshooting

### Error: No videos to process
- Check that videos are in `data/videos/`
- Verify filename format matches expected pattern

### Error: Cannot detect objects
- Try lowering confidence threshold in `config/config.yaml`:
  ```yaml
  model:
    confidence_threshold: 0.4  # Try lower value
  ```

### Model download issues
On first run, HuggingFace will download the DETR model (~200MB). This is normal and only happens once.

## Quick Test Checklist

- [ ] Videos placed in `data/videos/`
- [ ] Filenames follow correct format
- [ ] ROI coordinates configured
- [ ] Test run with 1 video succeeds
- [ ] Annotated output video generated
