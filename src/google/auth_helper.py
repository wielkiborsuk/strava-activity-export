import os
import yaml
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from logging_config import get_logger

logger = get_logger(__name__)


class CredentialHandler:
    """Handles Google OAuth2 credentials for Google API services"""

    def __init__(self, credentials_file: str):
        """
        Initialize credential handler with credentials file path.

        Args:
            credentials_file: Path to credentials YAML file for persistence
        """
        self.credentials_file = credentials_file

    def load_from_file(self) -> Optional[Dict]:
        """
        Load credentials from YAML file.

        Returns:
            Credentials dict or None if file doesn't exist
        """
        try:
            if not self.credentials_file or not os.path.exists(self.credentials_file):
                return None

            with open(self.credentials_file, 'r') as f:
                credentials_data = yaml.safe_load(f)

            return credentials_data
        except Exception as e:
            logger.warning(f"Failed to load credentials from file: {e}")
            raise

    def get_credentials(self) -> Credentials:
        """
        Get OAuth2 credentials, with automatic token refresh.

        Args:
            email_address: Gmail address

        Returns:
            Valid OAuth2 credentials
        """
        try:
            # Load credentials from file
            credentials_data = self.load_from_file()

            # Get client credentials from file
            client_id = credentials_data.get('client_id')
            client_secret = credentials_data.get('client_secret')
            token_uri = credentials_data.get('token_uri') or 'https://oauth2.googleapis.com/token'

            access_token = credentials_data.get('access_token')
            refresh_token = credentials_data.get('refresh_token')

            # Try to use provided access tokens with refresh token
            if refresh_token:
                credentials = Credentials(
                    token=access_token,
                    refresh_token=refresh_token,
                    client_id=client_id,
                    client_secret=client_secret,
                    token_uri=token_uri
                )

                # Check if token is expired and refresh if needed
                if credentials.expired and refresh_token:
                    logger.info("Access token expired, refreshing...")
                    credentials.refresh(Request())

                    # Save refreshed credentials if file path provided
                    self.save_credentials(credentials)

                    # Update access token if refreshed
                    if credentials.token != access_token:
                        logger.info("Token refreshed successfully")
                        access_token = credentials.token
            else:
                credentials = Credentials(token=access_token)

            return credentials
        except Exception as e:
            raise CredentialError(f"Failed to get credentials: {e}")

    def save_credentials(self, credentials: Credentials):
        """
        Save credentials to a YAML file for persistence.

        Args:
            credentials: Credentials object to save
        """
        try:
            credentials_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }

            # Save to file
            with open(self.credentials_file, 'w') as f:
                yaml.dump(credentials_data, f, default_flow_style=False)

            logger.info(f"Credentials saved to {self.credentials_file}")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")


class CredentialError(Exception):
    """Raised when credentials are missing or invalid."""
    pass
