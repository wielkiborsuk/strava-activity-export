#!/usr/bin/env python3
"""
Strava Browser Automation - Archive Request Trigger

This script automates the Strava archive download request process:
1. Login to Strava using email
2. Navigate to download_my_account page
3. Click the request-archive button
4. Verify success message

Usage as module:
    from download_account import run_archive_request
    success = run_archive_request(
        email="your@email.com",
        mode="production",
        headless=True
    )
"""

import sys
from pathlib import Path
import dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from strava.browser_config import BrowserConfig
from strava.browser_automation import BrowserAutomation
from strava.strava_browser import StravaBrowser

from google.gmail import GmailChecker

def run_archive_request(
    email: str = "",
    mode: str = "debug",
    pause: int = 10,
    verbose: bool = True,
    headless: bool = None,
) -> bool:
    """
    Run the Strava archive request workflow.

    Args:
        email: Strava email address (required if not in .env)
        mode: Browser mode - 'debug' for manual inspection or 'production' for automatic
        pause: Manual pause timeout in seconds (for debug mode)
        verbose: Enable verbose logging
        headless: Override headless mode (True/False/None for default)

    Returns:
        True if workflow completed successfully, False otherwise
    """
    print("=" * 60)
    print("Strava Browser Automation - Archive Request")
    print("=" * 60)

    # Load configuration
    print("\n[Configuration]")
    print(f"Mode: {mode}")

    env_config = BrowserConfig()

    # Build configuration dictionary
    config = {}

    # Set mode-specific configuration
    if mode == 'debug':
        config['headless'] = False
        config['pause_on_action'] = True
        config['manual_pause_timeout'] = pause
        config['verbose'] = verbose
    else:
        config['headless'] = True
        config['pause_on_action'] = False
        config['manual_pause_timeout'] = 0
        config['verbose'] = True

    # Override with provided parameters
    if headless is not None:
        config['headless'] = headless

    # Override with provided credentials
    if email:
        config['email'] = email
    else:
        config['email'] = os.getenv("STRAVA_EMAIL", "")

    # Merge with environment configuration
    merged = {**env_config.to_dict(), **config}
    config = BrowserConfig(merged)

    print(f"Headless: {config.get('headless', False)}")
    print(f"Manual Pause: {config.get('manual_pause_timeout', 10)} seconds")
    print(f"Verbose: {config.get('verbose', True)}")

    # Validate email
    email = config.get('email', env_config.get('email'))

    if not email:
        print("\n[Error] Email is required")
        print("Please set STRAVA_EMAIL in .env file")
        return False

    print(f"\nEmail: {email}")

    checker = GmailChecker()

    # Initialize browser automation
    print("\n[Initialization]")
    try:
        with BrowserAutomation(config) as browser:
            browser.initialize_browser()
            # Create Strava browser automation
            strava_browser = StravaBrowser(browser)

            # Run archive request workflow
            print("\n[Workflow]")
            print("\n[Step 1] Login to Strava")
            login_initiated = strava_browser.initiate_login(email)
            if not login_initiated:
                print("[Error] Login failed")
                return False

            otp_code = checker.search_strava_code_emails()[0]['code']

            login_success = strava_browser.finalize_login(otp_code)

            if not login_success:
                print("[Error] Login failed")
                return False

            print("\n[Step 2] Request archive extraction")
            extract_success = strava_browser.request_extract()

            # Output results
            print("\n" + "=" * 60)
            if login_success and extract_success:
                print("[Success] Archive request workflow completed")
                print("The archive download should be available via email soon")
            else:
                print("[Error] Archive request workflow failed")
            print("=" * 60)

            return login_success and extract_success

    except KeyboardInterrupt:
        print("\n\n[Interrupted] Workflow cancelled by user")
        return False
    except Exception as e:
        print(f"\n[Error] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_archive_request("wielki.borsuk@gmail.com")
