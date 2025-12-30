# 📹 Video File Instructions

## Where to Place Your Videos

**Directory:** `data/videos/`

Place all your video files in this directory.

## Video File Naming Format

Your videos MUST follow this naming convention:
```
{drawer_id}_{YYYYMMDD}_{HHMMSS}.mp4
```

**Examples:**
- `partition_1_20250126_143022.mp4` ✅
- `partition_2_20250127_091500.mp4` ✅
- `drawer_a_20250128_120000.mp4` ✅

**IMPORTANT:** 
- The timestamp format is: `YYYYMMDD_HHMMSS`
- Date: 8 digits (YYYYMMDD)
- Time: 6 digits (HHMMSS)
- Use underscores to separate

## Drawer IDs

Make sure your drawer_id matches one of the drawer IDs in `config/config.yaml`:

```yaml
drawers:
  partition_1:    # Use this in filename
    name: "Section A - Screws"
  partition_2:    # Or this
    name: "Section B - Bolts"
  partition_3:    # Or this
    name: "Section C - Nuts"
```

## Quick Test

Once you have videos placed in `data/videos/`, run:

```bash
# Process all videos
python main.py --process-all

# Or process a specific video
python main.py --video data/videos/your_video.mp4
```

## Expected Output

- Annotated videos in: `data/outputs/videos/`
- Alert images in: `data/outputs/frames/`
- Database in: `data/inventory_tracking.db`
- Logs in: `logs/inventory_monitor.log`
