#!/usr/bin/env python3
"""
Strava Archive Analysis Script - Extract and Analyze Data

This script performs the following workflow:
1. Find archive/extract email from Gmail
2. Download the archive based on URL provided in email
3. Extract archive contents to tmp_extract directory

Usage as module:
    from analyze_extract import run_analyze_extract
    success = run_analyze_extract(
        email="your@email.com",
        mode="debug",
        headless=True
    )
"""

import sys
import tarfile
import zipfile
import locale
from typing import Optional, Dict, Any
import csv
from datetime import datetime
import requests

from google.gmail import GmailChecker


def find_archive_email(
    max_results: int = 5,
    sender: str = "no-reply@strava.com"
) -> Optional[dict]:
    """
    Find archive/extract email from Gmail.

    Args:
        max_results: Maximum number of results to search
        sender: Email sender to filter by

    Returns:
        Dictionary with email details, or None if not found
    """
    try:
        print("\n[Step 1] Finding archive email")

        # Initialize Gmail checker

        # Search for Strava code emails
        results = checker.search_emails(
            sender=sender,
            max_results=max_results
        )

        if not results:
            print("[Info] No archive emails found")
            return None

        # Find email with archive/download link
        for result in results:
            body = result.get('body', '')
            if 'archive' in body.lower() or 'download' in body.lower():
                print(f"[Info] Found archive email: {result.get('subject', '')}")
                return result

        print("[Info] No archive email found with archive/download keywords")
        return None

    except Exception as e:
        print(f"[Error] Finding archive email failed: {e}")
        return None


def download_archive(
    url: str,
    output_path: str = "archive.zip"
) -> bool:
    """
    Download archive from URL.

    Args:
        url: Archive download URL
        output_path: Path to save downloaded archive

    Returns:
        True if download successful, False otherwise
    """
    try:
        print(f"\n[Step 2] Downloading archive from {url}")

        # Create output directory if it doesn't exist
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Download the archive using requests
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Save the archive
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[Success] Archive downloaded to {output_path}")
        return True

    except Exception as e:
        print(f"[Error] Download failed: {e}")
        return False


def extract_archive(
    archive_path: str,
    extract_dir: str = "tmp_extract"
) -> bool:
    """
    Extract archive to specified directory.

    Args:
        archive_path: Path to archive file
        extract_dir: Directory to extract contents to

    Returns:
        True if extraction successful, False otherwise
    """
    try:
        print(f"\n[Step 3] Extracting archive to {extract_dir}")

        # Create extraction directory
        extract_path = Path(extract_dir)
        extract_path.mkdir(parents=True, exist_ok=True)

        # Check if archive exists
        if not Path(archive_path).exists():
            print(f"[Error] Archive not found: {archive_path}")
            return False

        # Determine archive type
        archive_ext = Path(archive_path).suffix.lower()

        if archive_ext == '.zip':
            print(f"[Info] Extracting ZIP archive...")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            print(f"[Success] Extracted to {extract_path}")

        elif archive_ext in ['.tar', '.gz', '.tgz', '.bz2', '.xz']:
            print(f"[Info] Extracting TAR archive...")
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
            print(f"[Success] Extracted to {extract_path}")

        else:
            print(f"[Error] Unsupported archive format: {archive_ext}")
            return False

        # List extracted contents
        contents = list(extract_path.iterdir())
        print(f"[Info] Extracted {len(contents)} files/directories")

        return True

    except Exception as e:
        print(f"[Error] Extraction failed: {e}")
        return False


def load_activities(extract_dir: str = "tmp_extract") -> list[Dict[str, Any]]:
    """
    Load activities from CSV file in extract directory.

    Args:
        extract_dir: Directory containing extracted archive

    Returns:
        List of activity dictionaries with required fields
    """
    try:
        print(f"\n[Step 4] Loading activities from {extract_dir}")

        activities_csv = Path(extract_dir) / "activities.csv"

        if not activities_csv.exists():
            print(f"[Error] Activities CSV not found: {activities_csv}")
            return []

        # Read CSV with proper encoding
        activities = []
        with open(activities_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                start_date_str = row.get("Data aktywności", "")
                start_date = None
                locale.setlocale(locale.LC_TIME, "pl_PL.UTF-8")
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, "%d %b %Y, %H:%M:%S").isoformat()

                activity = {
                    "id": row.get("Identyfikator aktywności", ""),
                    "start_date": start_date,
                    "type": row.get("Rodzaj aktywności", ""),
                    "name": row.get("Nazwa aktywności", ""),
                    "distance": float(row.get("Dystans", 0)) if row.get("Dystans") else 0.0,
                    "moving_time": int(float(row.get("Czas ruchu", 0))) if row.get("Czas ruchu") else 0,
                    "elapsed_time": int(float(row.get("Czas całkowity", 0))) if row.get("Czas całkowity") else 0,
                    "average_speed": float(row.get("Średnia prędkość", 0)) if row.get("Średnia prędkość") else 0.0,
                    "max_speed": float(row.get("Maksymalna prędkość", 0)) if row.get("Maksymalna prędkość") else 0.0,
                }
                activities.append(activity)

        print(f"[Success] Loaded {len(activities)} activities")
        return activities

    except Exception as e:
        print(f"[Error] Loading activities failed: {e}")
        return []


def run_analyze_extract() -> bool:
    """
    Run the Strava archive analysis workflow.

    Returns:
        True if workflow completed successfully, False otherwise
    """
    print("=" * 60)
    print("Strava Archive Analysis - Extract and Analyze")
    print("=" * 60)

    # Step 1: Find archive email
    checker = GmailChecker(credentials_file="credentials.yaml")
    archive_email = checker.search_strava_export_emails()[0]

    if not archive_email:
        print("\n[Error] No archive email found")
        return False

    download_url = archive_email["download_url"]
    print(f"[Info] Download URL: {download_url}")

    # Step 2: Download archive
    archive_path = "strava_archive.zip"
    download_success = download_archive(download_url, archive_path)

    if not download_success:
        print("\n[Error] Archive download failed")
        return False

    # Step 3: Extract archive
    extract_success = extract_archive(archive_path, "tmp_extract")

    # Step 4: Load activities
    activities = load_activities("tmp_extract")

    # Output results
    print("\n" + "=" * 60)
    if archive_email and download_success and extract_success:
        print("[Success] Archive analysis workflow completed")
        print(f"Extracted to: {Path('tmp_extract').absolute()}")
    else:
        print("[Error] Archive analysis workflow failed")
    print("=" * 60)
    print(activities[:10])

    return archive_email and download_success and extract_success and activities


if __name__ == "__main__":
    success = run_analyze_extract()

    sys.exit(0 if success else 1)
