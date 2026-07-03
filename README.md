# Strava Activities Extraction (GCP Cloud Function)

This Cloud Function extracts activity information from the Strava API. It uses OAuth2 with a refresh token flow to maintain persistent access.

## Browser Automation (Alternative Data Collection)

For data extraction when the API is unavailable, you can use the browser automation tool to trigger a full account archive download.

### Prerequisites

1. Install Firefox browser
   - Ubuntu/Debian: `sudo apt-get install firefox`
   - macOS: `brew install firefox`
   - Windows: Download from https://www.mozilla.org/firefox/

2. Install geckodriver
   - Ubuntu/Debian: `sudo apt-get install geckodriver`
   - macOS: `brew install geckodriver`
   - Windows: Download from https://github.com/mozilla/geckodriver/releases

3. Install Python dependencies
   ```bash
   uv pip install -r browser_requirements.txt
   ```

### Setup

1. Configure credentials in `.env`:
   ```bash
   STRAVA_EMAIL="your@email.com"
   STRAVA_PASSWORD="yourpassword"
   ```

### Usage

### API Extraction (Cloud Function)
1. Create a Strava application at [strava.com/settings/api](https://www.strava.com/settings/api).
2. Note your **Client ID** and **Client Secret**.
3. Perform the initial manual authorization to get a **Refresh Token**:
   - Visit: `https://www.strava.com/oauth/authorize?client_id=[CLIENT_ID]&redirect_uri=http://localhost&response_type=code&scope=activity:read_all`
   - Authorize and copy the `code` from the redirect URL (e.g., `http://localhost/?state=&code=ABC123XYZ...`).
   - Exchange the code for tokens:
     ```bash
     curl -X POST https://www.strava.com/oauth/token \
       -F client_id=[CLIENT_ID] \
       -F client_secret=[CLIENT_SECRET] \
       -F code=[CODE] \
       -F grant_type=authorization_code
     ```
   - Copy the `refresh_token` from the response.

### Browser Automation Usage
```bash
# Debug mode with manual verification
python download_account.py --mode=debug

# Production mode (automatic)
python download_account.py --mode=production

# Custom settings
python download_account.py --mode=debug --pause=15 --verbose=true
```

### 1. Browser Automation Setup
1. Install Firefox browser
   - Ubuntu/Debian: `sudo apt-get install firefox`
   - macOS: `brew install firefox`
   - Windows: Download from https://www.mozilla.org/firefox/

2. Install geckodriver
   - Ubuntu/Debian: `sudo apt-get install geckodriver`
   - macOS: `brew install geckodriver`
   - Windows: Download from https://github.com/mozilla/geckodriver/releases

3. Install Python dependencies
   ```bash
   uv pip install -r browser_requirements.txt
   ```

### 2. Strava API Setup
1. Enable **Cloud Firestore** in your GCP project (managed under "Databases" -> "Firestore" in the GCP Console).
2. Create a collection named `config` and a document within it named `secrets`.
3. Add your parameters as fields in the `secrets` document:
   - `STRAVA_CLIENT_ID`
   - `STRAVA_CLIENT_SECRET`
   - `STRAVA_REFRESH_TOKEN`
4. Ensure the Cloud Function's service account has the following roles:
   - `Cloud Datastore User` (provides access to Firestore)

## Deployment

Deploy the function using the following command:

```bash
gcloud functions deploy extract_strava_activities \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point extract_strava_activities \
  --set-env-vars GCP_PROJECT=[YOUR_PROJECT_ID]
```

## Local Development

### 1. Setup Environment
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file based on the example:
```bash
cp .env.example .env
```
Fill in your Strava credentials in the `.env` file.

### 3. Run Locally
Use the Functions Framework to start the local server:
```bash
functions-framework --target=extract_strava_activities --debug
```

The function will be available at `http://localhost:8080`.

## Usage

### API Extraction
Once deployed, you can trigger the function via HTTP:

```bash
curl https://[REGION]-[PROJECT_ID].cloudfunctions.net/extract_strava_activities?per_page=5
```

### Parameters
- `per_page`: Number of activities to return (default 30).
- `page`: Page number (default 1).

### Browser Automation
```bash
# Debug mode with manual verification
python download_account.py --mode=debug

# Production mode (automatic)
python download_account.py --mode=production

# Custom settings
python download_account.py --mode=debug --pause=15 --verbose=true
```

### Parameters
- `--mode`: Browser mode (debug/production, default: debug)
- `--pause`: Manual pause timeout in seconds (default: 10)
- `--verbose`: Enable verbose logging (default: True)
- `--headless`: Override headless mode (true/false)
