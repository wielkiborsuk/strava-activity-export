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
import os
import dotenv
from src.logging_config import get_logger, log_info, log_error, log_success, log_info_structured

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from strava.browser_config import BrowserConfig
from strava.browser_automation import BrowserAutomation
from strava.strava_browser import StravaBrowser

from google.gmail import GmailChecker

logger = get_logger(__name__)

def run_archive_request(
    email: str = "",
    mode: str = "debug",
    verbose: bool = True,
    headless: bool = None,
) -> bool:
    """
    Run the Strava archive request workflow.

    Args:
        email: Strava email address (required if not in .env)
        mode: Browser mode - 'debug' for manual inspection or 'production' for automatic
        verbose: Enable verbose logging
        headless: Override headless mode (True/False/None for default)

    Returns:
        True if workflow completed successfully, False otherwise
    """
    log_info_structured("Strava Browser Automation - Archive Request")

    # Load configuration
    log_info("\n[Configuration]")
    log_info_structured({"mode": mode})

    env_config = BrowserConfig()

    # Build configuration dictionary
    config = {}

    # Set mode-specific configuration
    if mode == 'debug':
        config['headless'] = False
        config['verbose'] = verbose
    else:
        config['headless'] = True
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

    log_info_structured({"headless": config.get('headless', False), "verbose": config.get('verbose', True)})

    # Validate email
    email = config.get('email', env_config.get('email'))

    if not email:
        log_error("Email is required")
        log_error("Please set STRAVA_EMAIL in .env file")
        return False

    log_info(f"\nEmail: {email}")

    checker = GmailChecker(credentials_file="credentials.yaml")

    # Initialize browser automation
    log_info("\n[Initialization]")
    try:
        with BrowserAutomation(config) as browser:
            browser.initialize_browser()
            # Create Strava browser automation
            strava_browser = StravaBrowser(browser)

            # Run archive request workflow
            log_info("\n[Workflow]")
            log_info("\n[Step 1] Login to Strava")
            login_initiated = strava_browser.initiate_login(email)
            if not login_initiated:
                log_error("Login failed")
                return False

            otp_code = checker.search_strava_code_emails()[0]['code']

            login_success = strava_browser.finalize_login(otp_code)

            if not login_success:
                log_error("Login failed")
                return False

            log_info("\n[Step 2] Request archive extraction")
            extract_success = strava_browser.request_extract()

            # Output results
            log_info("\n" + "=" * 60)
            if login_success and extract_success:
                log_success("Archive request workflow completed")
                log_info("The archive download should be available via email soon")
            else:
                log_error("Archive request workflow failed")
            log_info("=" * 60)

            return login_success and extract_success

    except KeyboardInterrupt:
        log_info("\n\n[Interrupted] Workflow cancelled by user")
        return False
    except Exception as e:
        log_error(f"\n[Error] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_archive_request("wielki.borsuk@gmail.com")
