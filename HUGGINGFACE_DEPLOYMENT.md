# Deploying to Hugging Face Spaces

This guide shows you how to deploy the Stock Research Dashboard to Hugging Face Spaces for free!

## Why Hugging Face Spaces?

- ✅ **Completely Free** - No credit card required
- ✅ **Perfect for AI Demos** - Built for showcasing AI/ML applications
- ✅ **Always Online** - No sleeping or cold starts
- ✅ **Easy Sharing** - Get a public URL instantly
- ✅ **Version Control** - Built on Git

## Prerequisites

1. A Hugging Face account (free) - Sign up at https://huggingface.co/join
2. Your Google Cloud credentials (google.json file)
3. This repository

## Step-by-Step Deployment

### 1. Create a New Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in the details:
   - **Space name**: `stock-research-dashboard` (or your preferred name)
   - **License**: MIT
   - **Select SDK**: Choose **"Docker"**
   - **Space hardware**: CPU basic (free tier)
   - **Visibility**: Public or Private (your choice)
4. Click **"Create Space"**

### 2. Clone Your Space Repository

After creating the Space, you'll get a Git repository URL. Clone it:

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/stock-research-dashboard
cd stock-research-dashboard
```

### 3. Copy Your Project Files

Copy all files from this cxodemo repository to your Space repository:

```bash
# From the cxodemo directory
cp -r * /path/to/stock-research-dashboard/
```

Or manually copy these files:
- `app.py`
- `requirements.txt`
- `Dockerfile`
- `.dockerignore`
- `templates/` (entire folder)
- `README.md`
- `.gitignore`

### 4. Set Up Secrets (Environment Variables)

Hugging Face Spaces uses "Secrets" for sensitive data. You need to add your Google Cloud credentials:

**Option A: Using the Web Interface (Recommended)**

1. Go to your Space settings: `https://huggingface.co/spaces/YOUR_USERNAME/stock-research-dashboard/settings`
2. Scroll to **"Repository secrets"**
3. Add the following secrets:

   **Secret 1: GOOGLE_APPLICATION_CREDENTIALS**
   - Name: `GOOGLE_APPLICATION_CREDENTIALS`
   - Value: Paste the **entire contents** of your `google.json` file

   **Secret 2: GOOGLE_PROJECT_ID**
   - Name: `GOOGLE_PROJECT_ID`
   - Value: Your GCP project ID (e.g., `gemini-423216`)

   **Secret 3: GOOGLE_LOCATION**
   - Name: `GOOGLE_LOCATION`
   - Value: `us-central1` (or your preferred region)

   **Secret 4: GEMINI_MODEL** (optional)
   - Name: `GEMINI_MODEL`
   - Value: `gemini-2.0-flash-exp` (or your preferred model)

**Option B: Using Environment Variables File**

1. Create a `.env` file with your secrets
2. Add it to `.gitignore` (already done)
3. Upload it via the Files interface in Spaces

### 5. Update Dockerfile for Credentials

Since Spaces handles credentials as environment variables, we need to create the credentials file at runtime.

The Dockerfile is already configured, but make sure your `google.json` credentials are available as a secret.

### 6. Push to Hugging Face

```bash
cd /path/to/stock-research-dashboard

# Add all files
git add .

# Commit
git commit -m "Initial deployment: Stock Research Dashboard with Gemini AI"

# Push to Hugging Face
git push
```

### 7. Wait for Build

- Hugging Face will automatically build your Docker container
- This takes 5-10 minutes on first deploy
- Watch the build logs in your Space's page
- Once complete, your app will be live!

### 8. Access Your Live App

Your app will be available at:
```
https://huggingface.co/spaces/YOUR_USERNAME/stock-research-dashboard
```

## Handling Google Cloud Credentials in Spaces

Since Spaces uses secrets (environment variables) and we need a JSON file, we have two options:

### Option 1: Create credentials file from environment variable

Add this to the top of `app.py` (after imports):

```python
# Handle credentials in Hugging Face Spaces
if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
    import json
    creds_path = 'google_credentials.json'
    with open(creds_path, 'w') as f:
        json.dump(json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')), f)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
```

Then in Spaces secrets, add:
- Name: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
- Value: Your entire `google.json` contents as a single line

### Option 2: Upload credentials file directly

1. In your Space, go to "Files and versions"
2. Click "Add file" > "Upload files"
3. Upload your `google.json` (rename to `google_credentials.json`)
4. Update `.dockerignore` to allow this file:
   ```
   # In .dockerignore, change:
   *.json
   # To:
   !google_credentials.json
   ```

## Testing Your Deployment

Once deployed:

1. Open your Space URL
2. Select a stock from the dropdown (e.g., RELIANCE)
3. View the charts and metrics
4. Click "Generate Report" to test Gemini AI integration
5. Verify the report generates successfully

## Troubleshooting

### Issue: "Gemini AI not configured" warning

**Solution**: Check that your secrets are properly set:
- Go to Space Settings > Repository secrets
- Verify all required secrets are present
- Make sure there are no extra spaces or newlines

### Issue: Build fails

**Solution**: Check the build logs:
- Click on "Logs" tab in your Space
- Look for error messages
- Common issues:
  - Missing dependencies in `requirements.txt`
  - Port configuration (should be 7860)
  - Python version mismatch

### Issue: App loads but reports fail

**Solution**: Credentials issue
- Verify `GOOGLE_APPLICATION_CREDENTIALS_JSON` secret
- Check that your service account has Vertex AI permissions
- Ensure the project ID matches your GCP project

### Issue: Data caching not working

**Solution**:
- Spaces have ephemeral storage
- Cache will reset on rebuild
- This is normal and expected
- First load will fetch data from yfinance

## Updating Your Space

To update your deployed app:

```bash
# Make changes locally
cd /path/to/stock-research-dashboard

# Commit changes
git add .
git commit -m "Update: description of changes"

# Push to Hugging Face
git push
```

Spaces will automatically rebuild and redeploy!

## Cost

**Completely FREE!** 🎉

Hugging Face Spaces provides:
- Free CPU hosting
- No time limits
- No sleeping
- Unlimited rebuilds
- Public sharing

The only cost is your Google Cloud Vertex AI usage (which has a generous free tier).

## Sharing Your Demo

Once deployed, share your Space:

- **Direct Link**: `https://huggingface.co/spaces/YOUR_USERNAME/stock-research-dashboard`
- **Embed**: Hugging Face provides embed codes for websites
- **QR Code**: Generate a QR code for the URL for easy mobile access

Perfect for CEO demos! 🚀

## Alternative: Duplicate Space

If you want others to try your app with their own credentials:

1. Go to your Space
2. Click the "⋮" menu > "Duplicate this Space"
3. Others can clone and add their own credentials
4. Great for workshops or team demos

## Resources

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Docker Spaces Guide](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Environment Variables in Spaces](https://huggingface.co/docs/hub/spaces-overview#managing-secrets)

---

**Need Help?**
- Check the Hugging Face Spaces Discord: https://discord.gg/huggingface
- Open an issue in this repository
- Contact Hugging Face support

Happy deploying! 🤗
