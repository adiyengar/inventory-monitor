# Fix: "installer returned a non-zero exit code" Error

## What This Error Means

This error means one or more Python packages failed to install during Streamlit Cloud deployment. This is usually caused by:

1. **Large packages timing out** (torch, torchvision are ~2GB)
2. **Package version conflicts**
3. **Memory limitations** during installation
4. **Missing system dependencies**

## Root Cause

Your `app.py` (Streamlit frontend) **doesn't actually use** these heavy packages:
- ❌ `torch` / `torchvision` - only used in `main.py` for video processing
- ❌ `transformers` - only used in `main.py` for ML models
- ❌ `opencv-python` - only used in `main.py` for video processing
- ❌ `imageio`, `imageio-ffmpeg` - only used in `main.py`

**The Streamlit app only needs:**
- ✅ `streamlit` - the web framework
- ✅ `pyyaml` - for reading config.yaml
- ✅ `sqlalchemy` - for database operations
- ✅ `python-dateutil` - for date handling
- ✅ `python-dotenv` - for environment variables

## Solution: Use Minimal Requirements

I've created **two requirements files**:

1. **`requirements.txt`** (for Streamlit Cloud)
   - Minimal packages needed for the web interface only
   - **Use this for Streamlit Cloud deployment**

2. **`requirements-full.txt`** (for local development)
   - All packages including torch, opencv, etc.
   - **Use this when running `main.py` locally for video processing**

## Next Steps

### 1. Push the Updated requirements.txt

The `requirements.txt` file has been updated to only include minimal packages. Push this change:

```bash
git add requirements.txt requirements-streamlit.txt requirements-full.txt FIX_INSTALLER_ERROR.md
git commit -m "Fix Streamlit Cloud deployment - use minimal requirements"
git push origin main
```

### 2. Redeploy on Streamlit Cloud

1. Go to your Streamlit Cloud dashboard
2. The app should auto-redeploy, or click "Redeploy"
3. Installation should complete successfully now!

### 3. For Local Development with Video Processing

If you want to run `main.py` locally for video processing, install the full requirements:

```bash
pip install -r requirements-full.txt
```

## Why This Works

- **Streamlit Cloud**: Only installs what's needed for `app.py` (web interface)
  - Faster deployment (~1-2 minutes vs 10-15 minutes)
  - No timeout errors
  - Lower memory usage

- **Local Development**: You can still install full requirements for `main.py`
  - All ML packages available
  - Full video processing capabilities
  - Testing and development

## Architecture

```
┌─────────────────────────────────────────┐
│   Streamlit Cloud (app.py)              │
│   - Web interface                       │
│   - Upload videos                       │
│   - View statistics                     │
│   - Minimal requirements.txt            │
└─────────────────────────────────────────┘
                    │
                    │ (saves videos)
                    ▼
┌─────────────────────────────────────────┐
│   Local/Server (main.py)                │
│   - Video processing                    │
│   - ML model inference                  │
│   - Full requirements-full.txt          │
└─────────────────────────────────────────┘
```

## Alternative: If You Need ML in Streamlit Cloud

If you **really need** video processing in Streamlit Cloud, you can:

1. **Use lighter models:**
   ```python
   # In config/config.yaml
   model:
     name: "hustvl/yolos-tiny"  # Much smaller than detr-resnet-50
   ```

2. **Lazy load models:**
   - Only load ML models when needed
   - Cache models in Streamlit session state

3. **Use external API:**
   - Call a separate backend service for ML processing
   - Streamlit Cloud just handles the UI

## Troubleshooting

### Still Getting Errors?

1. **Check Streamlit Cloud logs** for specific package errors
2. **Remove optional packages** if any issues persist
3. **Verify Python version** in `runtime.txt` (3.11.7)

### Common Package Issues

- **torch/torchvision**: Too large, often times out
- **opencv-python**: Needs system libraries (use headless version)
- **pytest**: Not needed for production, remove if issues

