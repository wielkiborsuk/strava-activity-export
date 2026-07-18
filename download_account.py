#!/usr/bin/env python3
"""
Strava Browser Automation - Archive Request Trigger

This script automates the Strava archive download request process:
1. Login to Strava using email
2. Navigate to download_my_account page
3. Click the request-archive button
4. Verify success message

Usage:
    python download_account.py [options]
"""

import argparse
import sys
import os
from pathlib import Path
import dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from browser_config import BrowserConfig
from browser_automation import BrowserAutomation
from strava_browser import StravaBrowser


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Strava Browser Automation - Archive Request Trigger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Debug mode with manual verification
  python download_account.py --mode=debug

  # Production mode (automatic)
  python download_account.py --mode=production

  # Custom pause duration
  python download_account.py --mode=debug --pause=15

  # Headless mode
  python download_account.py --mode=production --headless=true
        """
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['debug', 'production'],
        default='debug',
        help='Browser mode: debug (manual inspection) or production (automatic)'
    )

    parser.add_argument(
        '--pause',
        type=int,
        default=10,
        help='Manual pause timeout in seconds (default: 10)'
    )

    parser.add_argument(
        '--verbose',
        type=lambda x: x.lower() in ('true', '1', 'yes'),
        default=True,
        help='Enable verbose logging (default: True)'
    )

    parser.add_argument(
        '--headless',
        type=str,
        choices=['true', 'false'],
        help='Override headless mode (true/false)'
    )

    parser.add_argument(
        '--email',
        type=str,
        help='Strava email (overrides .env)'
    )

    return parser.parse_args()


def load_config(args: argparse.Namespace, env_config: BrowserConfig) -> BrowserConfig:
    """
    Load configuration from arguments and environment.

    Args:
        args: Command-line arguments
        env_config: Environment configuration

    Returns:
        Complete configuration
    """
    config = {}

    # Set mode-specific configuration
    if args.mode == 'debug':
        config['headless'] = False
        config['pause_on_action'] = True
        config['manual_pause_timeout'] = args.pause
        config['verbose'] = args.verbose
    else:
        config['headless'] = True
        config['pause_on_action'] = False
        config['manual_pause_timeout'] = 0
        config['verbose'] = True

    # Override with command-line arguments
    if args.headless:
        config['headless'] = args.headless.lower() in ('true', '1', 'yes', 'on')

    # Override with command-line credentials
    if args.email:
        config['email'] = args.email
    else:
        config['email'] = os.getenv("STRAVA_EMAIL", "")

    # Merge with environment configuration
    merged = {**env_config.to_dict(), **config}

    return BrowserConfig(merged)


def main():
    """Main entry point."""
    print("=" * 60)
    print("Strava Browser Automation - Archive Request")
    print("=" * 60)

    # Parse arguments
    try:
        args = parse_arguments()
    except SystemExit:
        return

    # Load configuration
    print("\n[Configuration]")
    print(f"Mode: {args.mode}")

    env_config = BrowserConfig()
    config = load_config(args, env_config)

    print(f"Headless: {config.get('headless', False)}")
    print(f"Manual Pause: {config.get('manual_pause_timeout', 10)} seconds")
    print(f"Verbose: {config.get('verbose', True)}")

    # Get credentials
    email = config.get('email', env_config.get('email'))

    if not email:
        print("\n[Error] Email are required")
        print("Please set STRAVA_EMAIL in .env file")
        print("Or use --email argument")
        return

    print(f"\nEmail: {email}")

    # Initialize browser automation
    print("\n[Initialization]")
    try:
        with BrowserAutomation(config) as browser:
            browser.initialize_browser()
            # Create Strava browser automation
            strava_browser = StravaBrowser(browser)

            # Run archive request workflow
            print("\n[Workflow]")
            success = strava_browser.run_workflow(email, "")

            # Output results
            print("\n" + "=" * 60)
            if success:
                print("[Success] Archive request workflow completed")
                print("The archive download should be available via email soon")
            else:
                print("[Error] Archive request workflow failed")
            print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n[Interrupted] Workflow cancelled by user")
        return
    except Exception as e:
        print(f"\n[Error] Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
