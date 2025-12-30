# 🚀 Quick Start Guide

## 📍 Where to Load Your Videos Tomorrow

**Location:** `data/videos/`

Full path: `/Users/adisheshiyengar/Documents/inventory-monitor/data/videos/`

## 📝 Video File Naming (CRITICAL!)

Your video files MUST be named like this:

```
partition_1_20250126_140000.mp4
partition_2_20250126_140530.mp4
partition_3_20250126_141000.mp4
```

Format: `{drawer_id}_{YYYYMMDD}_{HHMMSS}.mp4`

- Use `partition_1`, `partition_2`, or `partition_3`
- Date: YYYYMMDD (8 digits)
- Time: HHMMSS (6 digits)
- Use underscores between parts

## ✅ Quick Test Commands

### 1. Place your videos
```bash
cd /Users/adisheshiyengar/Documents/inventory-monitor
cp ~/path/to/videos/*.mp4 data/videos/
```

### 2. Rename videos (if needed)
```bash
cd data/videos
# Rename to match format
mv your_video1.mp4 partition_1_20250126_140000.mp4
# ... etc
```

### 3. Test with ONE video first
```bash
python main.py --video data/videos/partition_1_20250126_140000.mp4
```

### 4. Process all 10 videos
```bash
python main.py --process-all
```

## 📊 Check Results

```bash
# See annotated videos
ls -lh data/outputs/videos/

# See alert images (if low inventory)
ls -lh data/outputs/frames/

# Check database
sqlite3 data/inventory_tracking.db "SELECT * FROM inventory_snapshots;"

# View logs
tail -f logs/inventory_monitor.log
```

## ⚙️ Before You Start

1. **Adjust ROI coordinates** in `config/config.yaml` based on your drawer layout
2. **Set thresholds** for each drawer (min and critical counts)
3. **Test email alerts** - make sure `.env` is configured

## 📞 Need Help?

- Logs: `logs/inventory_monitor.log`
- Configuration: `config/config.yaml`
- See `VIDEO_INSTRUCTIONS.md` for detailed naming rules
- See `TEST_GUIDE.md` for troubleshooting

## ⚡ System Status

✅ Model downloaded and ready  
✅ Database initialized  
✅ Email alerts configured  
✅ All dependencies installed  

**Ready to process videos!**
