import yaml
from pathlib import Path

def load_config(config_path_name: str = "config.yaml"):
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the config.yaml file

    Returns:
        Dictionary containing configuration data
    """
    config_path = Path(config_path_name)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config

def get_profile_config(config: dict, profile_name: str):
    """
    Get configuration for a specific profile.

    Args:
        config: Full configuration dictionary
        profile_name: Name of the profile to retrieve

    Returns:
        Dictionary containing profile-specific configuration
    """
    profiles = config.get('profiles', {})
    if profile_name not in profiles:
        raise ValueError(f"Profile '{profile_name}' not found in configuration")

    return profiles[profile_name]

def get_spreadsheet_config(config: dict):
    """
    Get spreadsheet configuration.

    Args:
        config: Full configuration dictionary

    Returns:
        Dictionary containing spreadsheet configuration
    """
    return config.get('spreadsheet', {})
