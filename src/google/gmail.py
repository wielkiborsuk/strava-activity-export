import base64
import re
import os
import logging
from email.message import EmailMessage
from typing import List, Dict, Optional, Tuple
from email.policy import default as email_policy
from googleapiclient.discovery import build
import requests
import yaml

try:
    from google.oauth2.credentials import Credentials
except ImportError:
    try:
        from google.auth.credentials import Credentials
    except ImportError:
        from google.oauth2.credentials import Credentials

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Strava email patterns
STRAVA_SENDER = 'no-reply@strava.com'
STRAVA_CODE_SUBJECT = 'Twój jednorazowy kod'
STRAVA_EXPORT_SUBJECT = 'Twoje archiwum Strava jest gotowe do pobrania'

class GmailChecker:
    """Main class for Gmail operations"""

    def __init__(
        self,
        credentials_file: str
    ):
        """
        Initialize Gmail client with credentials.

        Args:
            email_address: Gmail address (required)
            access_token: OAuth2 access token (required)
            refresh_token: OAuth2 refresh token (required)
            credentials_file: Path to credentials YAML file for persistence
        """
        self.service = None
        self.credentials = None
        self.credentials_file = credentials_file

        # Load credentials from file if provided
        credentials_data = self._load_credentials_from_file()
        if credentials_data:
            self.email_address = credentials_data.get('email')
            self.access_token = credentials_data.get('token')
            self.refresh_token = credentials_data.get('refresh_token')
            self.credentials_file = credentials_file

        if not self.email_address or not self.access_token:
            raise CredentialError("Missing Gmail credentials")

        # Initialize Gmail service
        self._initialize_service()

    def _get_client_credentials_from_file(self) -> Dict:
        """
        Get client credentials from credentials file.

        Returns:
            Dictionary with client_id, client_secret, and token_uri
        """
        try:
            if not self.credentials_file or not os.path.exists(self.credentials_file):
                return {}

            with open(self.credentials_file, 'r') as f:
                credentials_data = yaml.safe_load(f)

            return {
                'client_id': credentials_data.get('client_id'),
                'client_secret': credentials_data.get('client_secret'),
                'token_uri': credentials_data.get('token_uri')
            }
        except Exception as e:
            logger.warning(f"Failed to load client credentials from file: {e}")
            return {}

    def _initialize_service(self):
        """Initialize Gmail API service."""
        try:
            credentials = self._get_credentials()

            self.service = build('gmail', 'v1', credentials=credentials)

            logger.info(f"Gmail service initialized for {self.email_address}")
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize Gmail service: {e}")

    def _get_credentials(self) -> Credentials:
        """
        Get OAuth2 credentials, with automatic token refresh.

        Returns:
            Valid OAuth2 credentials
        """
        try:
            # Load credentials from file first
            credentials_data = self._load_credentials_from_file()

            # Get client credentials from file
            client_id = credentials_data.get('client_id')
            client_secret = credentials_data.get('client_secret')
            token_uri = credentials_data.get('token_uri') or 'https://oauth2.googleapis.com/token'

            # Try to use provided access tokens with refresh token
            if self.refresh_token:
                credentials = Credentials(
                    token=self.access_token,
                    refresh_token=self.refresh_token,
                    client_id=client_id,
                    client_secret=client_secret,
                    token_uri=token_uri
                )

                # Check if token is expired and refresh if needed
                if credentials.expired and credentials.refresh_token:
                    logger.info("Access token expired, refreshing...")
                    credentials.refresh(Request())

                    # Save refreshed credentials if file path provided
                    if self.credentials_file:
                        self._save_credentials(credentials)

                    # Update access token if refreshed
                    if credentials.token != self.access_token:
                        logger.info("Gmail token refreshed successfully")
                        self.access_token = credentials.token
            else:
                credentials = Credentials(token=self.access_token)

            return credentials
        except Exception as e:
            raise AuthenticationError(f"Failed to get credentials: {e}")

    def _save_credentials(self, credentials: Credentials):
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

    def _load_credentials_from_file(self) -> Optional[Dict]:
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
            return None

    def search_emails(
        self,
        sender: str = None,
        subject: str = None,
        max_results: int = 10,
        query: str = None
    ) -> List[EmailMessage]:
        """
        Search emails by sender and/or subject.

        Args:
            sender: Email sender filter
            subject: Email subject filter
            max_results: Maximum emails to return
            query: Custom search query

        Returns:
            List of EmailMessage objects
        """
        try:
            # Build search query
            search_query = []
            if sender:
                search_query.append(f'from:{sender}')
            if subject:
                search_query.append(f'subject:{subject}')
            if query:
                search_query.append(query)

            query_str = ' '.join(search_query) if search_query else ''

            logger.info(f"Searching Gmail for: {query_str}")

            results = self.service.users().messages().list(
                userId='me',
                q=query_str,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} emails")

            return messages
        except Exception as e:
            raise SearchError(f"Failed to search emails: {e}")

    def get_one_time_code_email(self, message_id: str) -> Optional[Dict]:
        """
        Extract 6-digit one-time code from email body.
        Expected pattern: "Twój jednorazowy kod" in subject
        Body format: Code followed by verification text

        Args:
            message_id: Gmail message ID

        Returns:
            dict with: {
                'code': str,
                'email': EmailMessage,
                'subject': str
            }
            or None if not found
        """
        try:
            message = self._get_message(message_id)
            subject = message.get('payload', {}).get('headers', [])
            subject_value = next((h['value'] for h in subject if h['name'] == 'Subject'), '')

            if STRAVA_CODE_SUBJECT not in subject_value:
                logger.debug(f"Message {message_id} is not a one-time code email")
                return None

            message_data = self._get_message(message_id)
            body_data = message_data.get('payload', {}).get('parts', {})[0].get('body', {}).get('data', '')

            if not body_data:
                logger.warning(f"No body found in message {message_id}")
                return None

            try:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            except Exception as e:
                logger.warning(f"Failed to decode message body: {e}")
                return None

            code = self._extract_one_time_code(body)

            if not code:
                logger.debug(f"No code found in message {message_id}")
                return None

            result = {
                'code': code,
                'email': message,
                'subject': subject_value
            }

            logger.info(f"Extracted code: {code} from message {message_id}")

            return result
        except Exception as e:
            logger.error(f"Failed to extract one-time code: {e}")
            return None

    def get_data_export_email(self, message_id: str) -> Optional[Dict]:
        """
        Extract download URL from Strava export email.
        Subject: "Twoje archiwum Strava jest gotowe do pobrania"

        Args:
            message_id: Gmail message ID

        Returns:
            dict with: {
                'download_url': str,
                'email': EmailMessage,
                'subject': str
            }
            or None if not found
        """
        try:
            message = self._get_message(message_id)
            subject = message.get('payload', {}).get('headers', [])
            subject_value = next((h['value'] for h in subject if h['name'] == 'Subject'), '')

            if STRAVA_EXPORT_SUBJECT not in subject_value:
                logger.debug(f"Message {message_id} is not a data export email")
                return None

            message_data = self._get_message(message_id)
            body_data = message_data.get('payload', {}).get('parts', [{}])[0].get('body', {}).get('data', '')

            if not body_data:
                logger.warning(f"No body found in message {message_id}")
                return None

            try:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            except Exception as e:
                logger.warning(f"Failed to decode message body: {e}")
                return None

            download_url = self._find_download_url(body)

            if not download_url:
                logger.debug(f"No download URL found in message {message_id}")
                return None

            result = {
                'download_url': download_url,
                'email': message,
                'subject': subject_value
            }

            logger.info(f"Extracted download URL: {download_url} from message {message_id}")

            return result
        except Exception as e:
            logger.error(f"Failed to extract download URL: {e}")
            return None

    def search_strava_code_emails(
        self,
        sender: str = STRAVA_SENDER,
        max_results: int = 10,
        query: str = None
    ) -> List[Dict]:
        """
        Convenience method: search for Strava one-time codes.

        Args:
            sender: Email sender filter (default: no-reply@strava.com)
            max_results: Maximum emails to return
            query: Custom search query

        Returns:
            List of code dictionaries
        """
        try:
            messages = self.search_emails(
                sender=sender,
                subject=STRAVA_CODE_SUBJECT,
                max_results=max_results,
                query=query
            )

            results = []
            for msg in messages:
                result = self.get_one_time_code_email(msg['id'])
                if result:
                    results.append(result)

            logger.info(f"Found {len(results)} one-time code emails")
            return results
        except Exception as e:
            logger.error(f"Failed to search Strava code emails: {e}")
            return []

    def search_strava_export_emails(
        self,
        sender: str = STRAVA_SENDER,
        max_results: int = 10,
        query: str = None
    ) -> List[Dict]:
        """
        Convenience method: search for Strava data exports.

        Args:
            sender: Email sender filter (default: no-reply@strava.com)
            max_results: Maximum emails to return
            query: Custom search query

        Returns:
            List of export dictionaries
        """
        try:
            messages = self.search_emails(
                sender=sender,
                subject=STRAVA_EXPORT_SUBJECT,
                max_results=max_results,
                query=query
            )

            results = []
            for msg in messages:
                result = self.get_data_export_email(msg['id'])
                if result:
                    results.append(result)

            logger.info(f"Found {len(results)} data export emails")
            return results
        except Exception as e:
            logger.error(f"Failed to search Strava export emails: {e}")
            return []

    def _get_message(self, message_id: str) -> Dict:
        """
        Get message details.

        Args:
            message_id: Gmail message ID

        Returns:
            Message dictionary
        """
        try:
            return self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
        except Exception as e:
            raise MessageNotFoundError(f"Failed to get message {message_id}: {e}")

    def _get_message_data(self, message_id: str) -> Dict:
        """
        Get message data including body.

        Args:
            message_id: Gmail message ID

        Returns:
            Message data dictionary
        """
        try:
            return self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='raw'
            ).execute()
        except Exception as e:
            raise MessageNotFoundError(f"Failed to get message data {message_id}: {e}")

    @staticmethod
    def _extract_one_time_code(body: str) -> Optional[str]:
        """
        Extract 6-digit code from text.

        Args:
            body: Email body text

        Returns:
            6-digit code or None
        """
        try:
            # Try multiple patterns
            patterns = [
                r'Code:\s*(\d{6})',
                r'Twój jednorazowy kod[:\s]*(\d{6})',
                r'verification code[:\s]*(\d{6})',
                r'kod[:\s]*(\d{6})',
                r'code[:\s]*(\d{6})',
                r'Your one-time code is[:\s]*(\d{6})',
            ]

            for pattern in patterns:
                match = re.search(pattern, body)
                if match:
                    code = match.group(1)
                    if re.match(r'^\d{6}$', code):
                        return code

            return None
        except Exception as e:
            logger.error(f"Failed to extract code: {e}")
            return None

    @staticmethod
    def _find_download_url(body: str) -> Optional[str]:
        """
        Find download URL in email body.

        Args:
            body: Email body text

        Returns:
            Download URL or None
        """
        try:
            # Try multiple patterns
            patterns = [
                r'https?://[^\s"\']+/strava/exports/[^"\s\'<>]*',
                r'https?://[^\s"\']+/archives/[^"\s\'<>]*',
                r'https?://[^\s"\']+/strava/[^"\s\'<>]*',
                r'https?://[^\s"\']+/exports/[^"\s\'<>]*',
                r'https?://[^\s"\']+/[a-z]+/exports/[^"\s\'<>]*',
                r'https://[^\s"\']+/strava.portability/athlete/[^"\s\'<>]*',
            ]

            for pattern in patterns:
                match = re.search(pattern, body)
                if match:
                    url = match.group(0)
                    # Validate URL format
                    try:
                        requests.head(url, timeout=5, allow_redirects=True)
                        return url
                    except requests.RequestException:
                        continue

            return None
        except Exception as e:
            logger.error(f"Failed to find download URL: {e}")
            return None

    @staticmethod
    def _validate_attachment_type(attachment) -> bool:
        """
        Validate attachment type.

        Args:
            attachment: Attachment object

        Returns:
            True if valid type
        """
        try:
            content_type = attachment.get('mimeType', '')
            valid_types = [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel',
                'application/zip',
                'application/x-zip-compressed',
                'application/x-zip',
            ]

            return content_type in valid_types
        except Exception as e:
            logger.error(f"Failed to validate attachment type: {e}")
            return False


class CredentialError(Exception):
    """Raised when credentials are missing or invalid."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(Exception):
    """Raised when token refresh fails."""
    pass


class SearchError(Exception):
    """Raised when search operation fails."""
    pass


class MessageNotFoundError(Exception):
    """Raised when message is not found."""
    pass


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    ch = GmailChecker(credentials_file="credentials.yaml")
    # mails = ch.search_emails(query="from:no-reply@strava.com")
    # print(mails)
    # m = ch._get_message(mails[0]['id'])
    # print(m)
    m = ch.search_strava_code_emails()
    print(m[0]['code'])

    # m = ch.search_strava_export_emails()
    # print(m[0]['download_url'])

