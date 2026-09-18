#!/usr/bin/env python3
"""
Strava Archive Analysis Script - Extract and Analyze Data

This script performs the following workflow:
1. Find archive/extract email from Gmail
2. Download the archive based on URL provided in email
3. Extract archive contents to tmp_extract directory
4. Load activities into structured format

Usage as module:
    from analyze_extract import run_analyze_extract
    activities = run_analyze_extract()
"""

from pathlib import Path
import sys
import tarfile
import zipfile
import locale
from typing import Dict, Any
import csv
from datetime import datetime
import requests
import tempfile
import argparse

from google.gmail import GmailChecker
from google.spreadsheet import append_activities
from config import load_config, get_profile_config


class ArchiveDownloadError(Exception):
    """Exception raised when archive download fails."""
    def __init__(self, message: str, url: str = ""):
        self.message = message
        self.url = url
        super().__init__(self.message)


class ArchiveExtractionError(Exception):
    """Exception raised when archive extraction fails."""
    def __init__(self, message: str, archive_path: str = ""):
        self.message = message
        self.archive_path = archive_path
        super().__init__(self.message)


class ActivitiesLoadingError(Exception):
    """Exception raised when loading activities fails."""
    def __init__(self, message: str, extract_dir: str = ""):
        self.message = message
        self.extract_dir = extract_dir
        super().__init__(self.message)


class ArchiveEmailNotFoundError(Exception):
    """Exception raised when archive email is not found."""
    def __init__(self, message: str = "No archive email found"):
        self.message = message
        super().__init__(self.message)

def download_archive(
    url: str,
    output_path: str = "archive.zip"
):
    """
    Download archive from URL.

    Args:
        url: Archive download URL
        output_path: Path to save downloaded archive

    Raises:
        ArchiveDownloadError: If download fails
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

    except requests.exceptions.RequestException as e:
        error_msg = f"Download failed for URL: {url}"
        raise ArchiveDownloadError(error_msg, url) from e
    except Exception as e:
        error_msg = f"Download failed: {e}"
        raise ArchiveDownloadError(error_msg, url) from e


def extract_archive(
    archive_path: str,
    extract_dir: str = "tmp_extract"
):
    """
    Extract archive to specified directory.

    Args:
        archive_path: Path to archive file
        extract_dir: Directory to extract contents to

    Raises:
        ArchiveExtractionError: If extraction fails
    """
    try:
        print(f"\n[Step 3] Extracting archive to {extract_dir}")

        # Create extraction directory
        extract_path = Path(extract_dir)
        extract_path.mkdir(parents=True, exist_ok=True)

        # Check if archive exists
        if not Path(archive_path).exists():
            error_msg = f"Archive not found: {archive_path}"
            print(f"[Error] {error_msg}")
            raise ArchiveExtractionError(error_msg, archive_path)

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
            error_msg = f"Unsupported archive format: {archive_ext}"
            print(f"[Error] {error_msg}")
            raise ArchiveExtractionError(error_msg, archive_path)

        # List extracted contents
        contents = list(extract_path.iterdir())
        print(f"[Info] Extracted {len(contents)} files/directories")

    except Exception as e:
        error_msg = f"Extraction failed: {e}"
        raise ArchiveExtractionError(error_msg, archive_path) from e


def load_activities(extract_dir: str = "tmp_extract") -> list[Dict[str, Any]]:
    """
    Load activities from CSV file in extract directory.

    Args:
        extract_dir: Directory containing extracted archive

    Returns:
        List of activity dictionaries with required fields

    Raises:
        ActivitiesLoadingError: If loading activities fails
    """
    try:
        print(f"\n[Step 4] Loading activities from {extract_dir}")

        activities_csv = Path(extract_dir) / "activities.csv"

        if not activities_csv.exists():
            error_msg = f"Activities CSV not found: {activities_csv}"
            print(f"[Error] {error_msg}")
            raise ActivitiesLoadingError(error_msg, extract_dir)

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
                    "id": int(row.get("Identyfikator aktywności", "")),
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

        activities = sorted(activities, key=lambda a: a.get('start_date', ''))

        print(f"[Success] Loaded {len(activities)} activities")
        return activities

    except Exception as e:
        error_msg = f"Loading activities failed: {e}"
        raise ActivitiesLoadingError(error_msg, extract_dir) from e


def run_analyze_extract(profile_name: str):
    """
    Run the Strava archive analysis workflow.

    Args:
        profile_name: Profile name to use (michal, antek)

    Returns:
        List of activity dictionaries with required fields

    Raises:
        ArchiveEmailNotFoundError: If no archive email is found
        ArchiveDownloadError: If download fails
        ArchiveExtractionError: If extraction fails
        ActivitiesLoadingError: If loading activities fails
    """
    print("=" * 60)
    print("Strava Archive Analysis - Extract and Analyze")
    print("=" * 60)

    try:
        config = load_config("config.yaml")
        profile_config = get_profile_config(config, profile_name)
        print(f"\n[Profile] Using profile: {profile_name}")
    except Exception as e:
        print(f"[Warning] Failed to load profile configuration: {e}")
        raise

    # Use temporary directory for archive and extracted files
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Step 1: Find archive email
            checker = GmailChecker(credentials_file=profile_config.get('credentials_file'))

            archive_email = checker.search_strava_export_emails()[0]

            if not archive_email:
                error_msg = "No archive email found"
                print("\n[Error] " + error_msg)
                raise ArchiveEmailNotFoundError(error_msg)

            download_url = archive_email["download_url"]
            print(f"[Info] Download URL: {download_url}")

            # Step 2: Download archive
            archive_path = Path(tmp_dir) / "strava_archive.zip"
            download_archive(download_url, str(archive_path))

            # Step 3: Extract archive
            extract_dir = Path(tmp_dir) / "tmp_extract"
            extract_archive(str(archive_path), str(extract_dir))

            # Step 4: Load activities - must be done before cleanup
            activities = load_activities(str(extract_dir))

            # Step 5: Append to Spreadsheet (Ensuring unique IDs)
            # Load spreadsheet credentials from config
            try:
                config_dict = load_config("config.yaml")
                spreadsheet_config = config_dict.get('spreadsheet', {})
            except Exception as e:
                print(f"[Warning] Failed to load spreadsheet configuration: {e}")
                raise

            spreadsheet_id = spreadsheet_config.get('spreadsheet_id')
            print(f"\n[Step 5] Appending activities to spreadsheet {spreadsheet_id}...")

            # Column definition for ordering and labels
            column_definition = [
                "id",
                "start_date",
                "type",
                "name",
                "distance",
                "moving_time",
                "elapsed_time",
                "average_speed",
                "max_speed",
            ]
            column_labels = {
                "id": "ID",
                "start_date": "Date",
                "type": "Activity Type",
                "name": "Activity Name",
                "distance": "Distance (m)",
                "moving_time": "Moving Time (s)",
                "elapsed_time": "Elapsed Time (s)",
                "average_speed": "Avg Speed (m/s)",
                "max_speed": "Max Speed (m/s)",
            }

            # Use sheet_name from profile if available
            sheet_name = profile_config.get('sheet_name')

            updated_rows = append_activities(
                spreadsheet_config.get('credentials_file'),
                spreadsheet_id,
                activities,
                sheet_name=sheet_name,
                column_definition=column_definition,
                column_labels=column_labels,
            )

            print(f"[Success] Added {updated_rows} new activities")

            # Output results
            print("\n" + "=" * 60)
            print("[Success] Archive analysis workflow completed")
            print(f"Extracted to: {extract_dir}")
            print("=" * 60)
            print(f"Activities loaded: {len(activities)}")

            return activities

    except Exception as e:
        print(f"\n[Error] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strava Archive Analysis - Extract and analyze activities")
    parser.add_argument("--profile", "-p", type=str, help="Profile name to use (michal, antek)")

    args = parser.parse_args()

    try:
        activities = run_analyze_extract(profile_name=args.profile)
        sys.exit(0 if activities else 1)
    except Exception as e:
        print(f"\n[Error] Main execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
