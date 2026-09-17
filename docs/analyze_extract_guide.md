# Strava Archive Analysis Script

## Overview

The `analyze_extract.py` script performs a complete workflow for downloading and analyzing Strava archive data:

1. **Find archive email** - Searches Gmail for archive/extract emails
2. **Download archive** - Downloads the archive from the URL in the email
3. **Extract archive** - Extracts archive contents to `tmp_extract` directory

## Features

- **Email Search**: Search Gmail for archive emails with keywords
- **Smart URL Extraction**: Automatically extracts download URLs from email bodies
- **Multi-format Support**: Supports ZIP, TAR, GZ, and other archive formats
- **Automatic Extraction**: Extracts archives to specified directory
- **Configurable**: Support for debug/production modes with optional manual inspection

## Usage

### Command Line

```bash
# Basic usage
python src/analyze_extract.py your-email@gmail.com

# Production mode (headless)
python src/analyze_extract.py your-email@gmail.com --mode production --headless

# Debug mode with manual inspection
python src/analyze_extract.py your-email@gmail.com --mode debug --pause 10

# With custom settings
python src/analyze_extract.py your-email@gmail.com \
    --mode production \
    --max-results 5 \
    --headless
```

### As a Module

```python
from src.analyze_extract import run_analyze_extract

# Run the workflow
success = run_analyze_extract(
    email="your-email@gmail.com",
    mode="production",
    headless=True,
    max_results=5
)

if success:
    print("Archive analysis completed successfully")
else:
    print("Archive analysis failed")
```

## Functions

### `find_archive_email(email, max_results, sender)`

Find archive/extract email from Gmail.

**Parameters:**
- `email`: Gmail address to search
- `max_results`: Maximum number of results to search (default: 5)
- `sender`: Email sender to filter by (default: "no-reply@strava.com")

**Returns:**
- Dictionary with email details, or None if not found

### `download_archive(url, output_path)`

Download archive from URL.

**Parameters:**
- `url`: Archive download URL
- `output_path`: Path to save downloaded archive

**Returns:**
- True if download successful, False otherwise

### `extract_archive(archive_path, extract_dir)`

Extract archive to specified directory.

**Parameters:**
- `archive_path`: Path to archive file
- `extract_dir`: Directory to extract contents to (default: "tmp_extract")

**Returns:**
- True if extraction successful, False otherwise

### `clean_extract_dir(extract_dir)`

Clean up extraction directory.

**Parameters:**
- `extract_dir`: Directory to clean (default: "tmp_extract")

### `run_analyze_extract(email, mode, pause, verbose, headless, max_results)`

Run the complete archive analysis workflow.

**Parameters:**
- `email`: Email address (required)
- `mode`: Browser mode - 'debug' for manual inspection or 'production' for automatic
- `pause`: Manual pause timeout in seconds (for debug mode)
- `verbose`: Enable verbose logging
- `headless`: Override headless mode (True/False/None for default)
- `max_results`: Maximum number of emails to search (default: 5)

**Returns:**
- True if workflow completed successfully, False otherwise

## Workflow

```
┌─────────────────┐
│ 1. Find Email    │
│    Search Gmail │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Download     │
│    Archive      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Extract      │
│    Archive      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Analyze      │
│    Contents     │
└─────────────────┘
```

## Configuration

### Environment Variables

Set `STRAVA_EMAIL` in `.env` file:

```bash
STRAVA_EMAIL=your-email@gmail.com
```

### Browser Configuration

The script uses the browser automation framework for downloading archives. Configure in `.env`:

```bash
# Browser Automation Configuration
BROWSER_HEADLESS=False
BROWSER_DEBUG_MODE=True
BROWSER_PAUSE_ON_ACTION=True
BROWSER_MANUAL_PAUSE_TIMEOUT=10
BROWSER_TIMEOUT=30
BROWSER_EXPLICIT_WAIT=10
BROWSER_VERBOSE=True
```

## Output

After successful execution:

```
[Success] Archive analysis workflow completed
Extracted to: /path/to/tmp_extract
```

The archive contents will be in the `tmp_extract` directory.

## Troubleshooting

### No Archive Email Found

1. **Check email**: Verify `STRAVA_EMAIL` is set correctly
2. **Check Gmail**: Ensure you have received the archive email
3. **Check keywords**: The script looks for "archive" or "download" in email body

### Download Failed

1. **Check URL**: Verify the download URL is correct
2. **Check network**: Ensure internet connection is available
3. **Check browser**: Verify browser automation is working

### Extraction Failed

1. **Check archive**: Verify archive file exists and is valid
2. **Check format**: Supported formats: ZIP, TAR, GZ, TGZ, BZ2, XZ
3. **Check permissions**: Ensure write permissions for extraction directory

## Integration with Strava Browser Automation

The script integrates with the Strava browser automation framework:

```python
from strava.strava_browser import StravaBrowser

# Use with StravaBrowser
strava_browser = StravaBrowser(browser)
archive_email = strava_browser.find_archive_email(email)
download_url = archive_email['body']
```

## Best Practices

1. **Use Production Mode**: Run in production mode for automatic execution
2. **Monitor Logs**: Check verbose output for debugging
3. **Clean Up**: Use `clean_extract_dir()` to remove temporary files
4. **Save Archives**: Keep downloaded archives for later analysis
5. **Check Results**: Verify extraction completed successfully

## Security Notes

- Keep credentials.yaml secure (add to .gitignore)
- Use environment variables for sensitive information
- Verify downloaded archives for malware
- Clean up temporary files after analysis

## Examples

### Example 1: Basic Usage

```bash
python src/analyze_extract.py wielki.borsuk@gmail.com
```

### Example 2: Production Mode with Headless

```bash
python src/analyze_extract.py wielki.borsuk@gmail.com --mode production --headless
```

### Example 3: Custom Settings

```bash
python src/analyze_extract.py wielki.borsuk@gmail.com --mode debug --pause 10 --max-results 10
```

### Example 4: As Module

```python
from src.analyze_extract import find_archive_email, download_archive, extract_archive

# Find archive email
email_result = find_archive_email(
    email="wielki.borsuk@gmail.com",
    max_results=5
)

if email_result:
    # Extract URL
    import re
    body = email_result['body']
    url_pattern = r'https?://[^\s<>"\'()]+'
    urls = re.findall(url_pattern, body)
    download_url = urls[0]

    # Download
    download_archive(download_url, "strava_archive.zip")

    # Extract
    extract_archive("strava_archive.zip", "tmp_extract")
```
