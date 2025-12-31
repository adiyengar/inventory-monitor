# Deployment Guide

## Project Setup Complete ✅

Your project has been packaged and prepared for GitHub. Here's what was added:

### New Files Created:
1. **`app.py`** - Streamlit web interface for video upload and management
2. **`setup.py`** - Package setup script for pip installation
3. **Updated `requirements.txt`** - Added streamlit dependency
4. **Updated `README.md`** - Added Streamlit usage instructions
5. **Updated `.gitignore`** - Excluded database file from version control

### Changes Committed:
All changes have been committed to your local repository with the message:
"Add Streamlit frontend, packaging setup, and update documentation"

## Push to GitHub

To push your changes to GitHub, run:

```bash
git push origin main
```

If you encounter authentication issues, you may need to:

1. **Use SSH instead of HTTPS:**
   ```bash
   git remote set-url origin git@github.com:adiyengar/inventory-monitor.git
   git push origin main
   ```

2. **Or use GitHub CLI:**
   ```bash
   gh auth login
   git push origin main
   ```

3. **Or use a personal access token:**
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Create a token with `repo` permissions
   - Use it when prompted for password

## Running the Streamlit App

After pushing, you can run the Streamlit interface:

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Installing as a Package

You can also install the project as a package:

```bash
pip install -e .
```

This allows you to use the `inventory-monitor` command from anywhere.

## Next Steps

1. Push to GitHub using one of the methods above
2. Test the Streamlit interface locally
3. Configure your drawer ROIs in `config/config.yaml`
4. Upload test videos through the web interface
5. Process videos and view statistics

