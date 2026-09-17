import os
import dotenv
from pathlib import Path
from typing import Dict, Any, Optional
from src.logging_config import get_logger, log_info

logger = get_logger(__name__)


class BrowserConfig:
    """Browser configuration management."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, env_path: Optional[str] = None):
        """
        Initialize browser configuration.

        Args:
            config: Optional configuration dictionary
            env_path: Optional path to .env file
        """
        self.config = self._load_config(config, env_path)

    def _load_config(self, config: Optional[Dict[str, Any]], env_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from dictionary and environment.

        Args:
            config: Optional configuration dictionary
            env_path: Optional path to .env file

        Returns:
            Complete configuration dictionary
        """
        # Determine the .env file path
        if env_path:
            dotenv_path = Path(env_path)
        else:
            # Default to .env file in the current directory
            dotenv_path = Path.cwd() / '.env'

        # Load dotenv file
        loaded = dotenv.load_dotenv(dotenv_path=dotenv_path)
        if loaded:
            log_info(f"Loaded .env file from: {dotenv_path}")

        if config is None:
            config = {}

        # Load from environment if not provided
        env_config = {
            'headless': self._get_env_bool('BROWSER_HEADLESS', False),
            'debug_mode': self._get_env_bool('BROWSER_DEBUG_MODE', True),
            'pause_on_action': self._get_env_bool('BROWSER_PAUSE_ON_ACTION', True),
            'manual_pause_timeout': self._get_env_int('BROWSER_MANUAL_PAUSE_TIMEOUT', 10),
            'timeout': self._get_env_int('BROWSER_TIMEOUT', 30),
            'explicit_wait': self._get_env_int('BROWSER_EXPLICIT_WAIT', 10),
            'verbose': self._get_env_bool('BROWSER_VERBOSE', True),
            'firefox_binary': self._get_env('BROWSER_FIREFOX_BINARY', '/snap/firefox/current/usr/lib/firefox/firefox'),
        }

        # Merge with provided config
        merged = {**env_config, **config}

        return merged

    def _get_env_bool(self, key: str, default: bool) -> bool:
        """
        Get boolean value from environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Boolean value
        """
        env_value = os.environ.get(key)
        if env_value:
            return env_value.lower() in ('true', '1', 'yes', 'on')
        return default

    def _get_env_int(self, key: str, default: int) -> int:
        """
        Get integer value from environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Integer value
        """
        env_value = os.environ.get(key)
        if env_value:
            try:
                return int(env_value)
            except ValueError:
                pass
        return default

    def _get_env(self, key: str, default: str = '') -> str:
        """
        Get string value from environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            String value
        """
        env_value = os.environ.get(key)
        if env_value:
            return env_value
        return default

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """
        Get configuration value using dictionary syntax.

        Args:
            key: Configuration key

        Returns:
            Configuration value
        """
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        """
        Check if configuration key exists.

        Args:
            key: Configuration key

        Returns:
            True if key exists
        """
        return key in self.config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config.copy()

    def __repr__(self) -> str:
        """
        String representation of configuration.

        Returns:
            Configuration string
        """
        return f"BrowserConfig({self.config})"
