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
        headless=True
    )
"""

import argparse
from logging_config import get_logger, log_info, log_error

from strava.browser_config import BrowserConfig
from strava.browser_automation import BrowserAutomation
from strava.strava_browser import StravaBrowser

from google.gmail import GmailChecker
from strava.browser_automation import (
    BrowserAutomationError,
    ElementNotFoundError,
    VerificationError,
    LoginError
)
from config import load_config, get_profile_config

logger = get_logger(__name__)

def run_archive_request(
    profile_name: str,
    headless: bool = False,
) -> bool:
    """
    Run the Strava archive request workflow.

    Args:
        email: Strava email address (required if not in .env)
        mode: Browser mode - 'debug' for manual inspection or 'production' for automatic
        verbose: Enable verbose logging
        headless: Override headless mode (True/False/None for default)
        profile_name: Profile name to use for credentials

    Returns:
        True if workflow completed successfully, False otherwise
    """
    log_info("Strava Browser Automation - Archive Request")

    try:
        config = load_config("config.yaml")
        profile_config = get_profile_config(config, profile_name)
        log_info(f"Profile: {profile_name}")
    except Exception as e:
        log_error(f"Failed to load profile configuration: {e}")
        raise

    # Build configuration dictionary
    browser_config = BrowserConfig()
    browser_config.config['headless'] = headless

    checker = GmailChecker(credentials_file=profile_config.get('credentials_file', "credentials.yaml"))

    # Initialize browser automation
    log_info("\n[Initialization]")
    try:
        with BrowserAutomation(browser_config.to_dict()) as browser:
            browser.initialize_browser()
            # Create Strava browser automation
            strava_browser = StravaBrowser(browser)

            # Run archive request workflow
            log_info("\n[Workflow]")
            log_info("\n[Step 1] Login to Strava")
            try:
                strava_browser.initiate_login(profile_config.get('email'))
            except (LoginError, ElementNotFoundError) as e:
                log_error(f"Login failed: {e}")
                return False

            otp_code = checker.search_strava_code_emails()[0]['code']

            try:
                strava_browser.finalize_login(otp_code)
            except LoginError as e:
                log_error(f"Login failed: {e}")
                return False

            log_info("\n[Step 2] Request archive extraction")
            try:
                strava_browser.request_extract()
            except VerificationError as e:
                log_error(f"Archive request extraction failed: {e}")
                return False

            # Output results
            log_info("\n" + "=" * 60)
            log_info("Archive request workflow completed")
            log_info("The archive download should be available via email soon")
            log_info("=" * 60)

            return True

    except KeyboardInterrupt:
        log_info("\n\n[Interrupted] Workflow cancelled by user")
        return False
    except BrowserAutomationError as e:
        log_error(f"\n[Error] Browser automation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strava Archive Request - Download and analyze activities")
    parser.add_argument("--profile", "-p", type=str, help="Profile name to use (michal, antek)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")

    args = parser.parse_args()

    # Run with profile if specified
    run_archive_request(profile_name=args.profile, headless=args.headless)
