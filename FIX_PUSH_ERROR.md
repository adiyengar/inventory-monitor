# Fix: Certificate/SSL Error When Pushing

## The Error
```
fatal: unable to access 'https://github.com/...': error setting certificate verify locations: CAfile: /etc/ssl/cert.pem CApath: none
```

## Solution 1: Use SSH Instead of HTTPS (Recommended)

I've already updated your remote to use SSH. Now you need to:

### Step 1: Set up SSH Key (if not already done)

1. Check if you have an SSH key:
   ```bash
   ls -la ~/.ssh
   ```
   Look for `id_rsa` or `id_ed25519` files

2. If you don't have one, create it:
   ```bash
   ssh-keygen -t ed25519 -C "adi@u.northwestern.edu"
   ```
   Press Enter to accept default location, then set a passphrase (optional)

3. Add your SSH key to GitHub:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   Copy the output, then:
   - Go to https://github.com/settings/keys
   - Click "New SSH key"
   - Paste your key and save

### Step 2: Test SSH Connection
```bash
ssh -T git@github.com
```
You should see: "Hi adiyengar! You've successfully authenticated..."

### Step 3: Push from GitHub Desktop
- The remote is now set to SSH
- Try pushing again in GitHub Desktop
- It should work now!

## Solution 2: Fix Certificate Issue (Alternative)

If you prefer to keep using HTTPS:

1. Update git to use system certificates:
   ```bash
   git config --global http.sslCAInfo /etc/ssl/cert.pem
   ```
   Or on macOS:
   ```bash
   git config --global http.sslCAInfo /usr/local/etc/openssl/cert.pem
   ```

2. Or disable SSL verification (NOT RECOMMENDED for security):
   ```bash
   git config --global http.sslVerify false
   ```

## Solution 3: Use GitHub Desktop's Built-in Authentication

GitHub Desktop should handle authentication automatically:

1. Make sure you're signed in:
   - **GitHub Desktop > Preferences > Accounts**
   - Verify you're signed in as `adiyengar`

2. Try pushing again - GitHub Desktop uses its own authentication

## Current Remote Configuration

Your remote is now set to SSH:
```
origin  git@github.com:adiyengar/inventory-monitor.git
```

## Quick Test

After setting up SSH, test the connection:
```bash
ssh -T git@github.com
```

If successful, you'll see a welcome message. Then try pushing in GitHub Desktop again.

