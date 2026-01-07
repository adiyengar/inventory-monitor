# Streamlit Cloud Deployment Guide

## Issues Fixed

### 1. Pip Version
- Removed pip from requirements.txt (Streamlit Cloud handles pip upgrades automatically)
- Changed `opencv-python` to `opencv-python-headless` to avoid GUI dependencies

### 2. OpenCV Headless Version
- Changed `opencv-python` to `opencv-python-headless` (required for Streamlit Cloud)
- Headless version doesn't require GUI dependencies

### 3. Package Version Flexibility
- Changed strict `==` to `>=` for most packages to allow Streamlit Cloud to resolve compatible versions
- Kept strict versions for `torch` and `torchvision` as they need to match

### 4. Python Version
- Created `runtime.txt` specifying Python 3.11.7
- This ensures consistent Python version on Streamlit Cloud

### 5. Streamlit Configuration
- Created `.streamlit/config.toml` with proper settings
- This configures the Streamlit app properly

## Deployment Steps

### Step 1: Push Changes to GitHub
Make sure all the new files are pushed:
```bash
git add requirements.txt runtime.txt .streamlit/config.toml packages.txt
git commit -m "Fix Streamlit Cloud deployment - update pip and dependencies"
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `adiyengar/inventory-monitor`
5. Select branch: `main`
6. Main file path: `app.py`
7. Click "Deploy"

### Step 3: Configure App Settings

In Streamlit Cloud settings:
- **Python version**: Should detect 3.11 from `runtime.txt`
- **App URL**: Will be assigned automatically
- **Secrets**: You can add environment variables here if needed

## Important Notes

### Large Packages
- `torch` and `torchvision` are very large (~2GB)
- First deployment may take 10-15 minutes
- Consider if you really need these for the Streamlit app

### Alternative: Lighter ML Models
If deployment is too slow, consider:
- Using smaller models (e.g., `yolos-tiny` instead of `detr-resnet-50`)
- Moving heavy ML processing to a separate backend
- Using Streamlit Cloud's file upload limits (200MB per file)

### Environment Variables
If you need to store secrets:
1. Go to Streamlit Cloud app settings
2. Click "Secrets"
3. Add key-value pairs (e.g., `SENDGRID_API_KEY`)

### File Storage
- Streamlit Cloud has limited file storage
- Uploaded videos will be stored temporarily
- Consider using external storage (S3, etc.) for production

## Troubleshooting

### "Pip version" error
- Streamlit Cloud automatically upgrades pip, so this should not be needed
- If you still get this error, check the deployment logs for the exact error message
- Try removing optional packages (like `pytest`) to see if that helps
- Make sure `runtime.txt` specifies a compatible Python version

### "Package installation failed"
- Check Streamlit Cloud logs
- Large packages like `torch` may timeout
- Consider removing testing packages in production

### "Module not found"
- Make sure all dependencies are in `requirements.txt`
- Check that `src/` directory is included in the repo

### "App crashes on startup"
- Check logs in Streamlit Cloud
- Verify `config/config.yaml` exists
- Make sure database path is writable

## File Structure for Streamlit Cloud

```
inventory-monitor/
├── app.py              # Main Streamlit app (required)
├── requirements.txt    # Dependencies (required)
├── runtime.txt        # Python version (optional but recommended)
├── packages.txt       # System packages (optional)
├── .streamlit/
│   └── config.toml    # Streamlit config (optional)
├── config/
│   └── config.yaml    # App configuration (required)
├── src/               # Source code (required)
└── README.md          # Documentation (recommended)
```

## After Deployment

Once deployed, your app will be available at:
`https://<your-app-name>.streamlit.app`

You can then:
- Upload videos through the web interface
- View statistics and reports
- Monitor inventory tracking

