# 📹 Video File Instructions

## Where to Place Your Videos

**Directory:** `data/videos/`

Place all your video files in this directory. Both `.mp4` and `.mov`/`.MOV`
are supported (configured via `video.video_extensions` in `config/config.yaml`).

## Video File Naming Format

Your videos MUST follow this naming convention:
```
{drawer_id}_{YYYYMMDD}_{HHMMSS}.{mp4|mov}
```

**Examples:**
- `partition_1_20250126_143022.mp4` ✅
- `partition_2_20250127_091500.mp4` ✅
- `drawer_a_20250128_120000.mov` ✅

**IMPORTANT:** 
- The timestamp format is: `YYYYMMDD_HHMMSS`
- Date: 8 digits (YYYYMMDD)
- Time: 6 digits (HHMMSS)
- Use underscores to separate
- The `{drawer_id}` prefix (e.g. `partition_1`) is just used to derive the
  video's timestamp for sorting/aging — it does **not** need to match a
  drawer id in `config/config.yaml`. Every configured drawer's ROI is
  checked against every video, regardless of filename.

## First-Time Setup: Drawing Partitions

Before your first real run, define where each partition/drawer is in the
frame. With a video already placed in `data/videos/`, run:

```bash
python main.py --setup
```

This first opens a frame picker on the newest video — drag the slider (or
press `a`/`d` to step frame-by-frame) to find a frame where the partitions
are actually visible (e.g. the drawer is open, not the closed frame at
`t=0`), then press `s` to select it. Then a drawing window opens on that
frame — click-drag a box over each partition, press `q` when done, then
answer a few prompts per box (display name, partition id, part type,
thresholds). It writes the result straight into `config/config.yaml`
(backing up the previous file as `config/config.yaml.bak`).

To use a specific video instead of the newest one:
```bash
python main.py --setup --video data/videos/your_video.mov
# or equivalently:
python scripts/find_roi.py data/videos/your_video.mov
```

If you already know which frame number shows the drawer open, skip the
picker entirely:
```bash
python main.py --setup --frame 142
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
