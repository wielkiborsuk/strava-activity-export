import base64
import re
import time
import logging
from email.message import EmailMessage
from typing import List, Dict, Optional, Tuple
from email.policy import default as email_policy
import requests

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

    def __init__(self, email_address: str = None, access_token: str = None):
        """
        Initialize Gmail client with credentials.

        Args:
            email_address: Gmail address (from env or provided)
            access_token: OAuth2 access token (from env or provided)
        """
        self.email_address = email_address
        self.access_token = access_token
        self.service = None
        self.credentials = None

        # Load credentials from environment if not provided
        if not email_address:
            self.email_address = self._get_env_value('GMAIL_EMAIL_ADDRESS')
        if not access_token:
            self.access_token = self._get_env_value('GMAIL_ACCESS_TOKEN')

        if not self.email_address or not self.access_token:
            raise CredentialError("Missing Gmail credentials")

        # Initialize Gmail service
        self._initialize_service()

    def _get_env_value(self, key: str) -> str:
        """
        Get environment variable value, first from local env then from config.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value
        """
        local_value = __import__('os').environ.get(key)
        if local_value:
            return local_value

        try:
            config_module = __import__('config')
            return config_module.get_secret(key)
        except Exception as e:
            logger.warning(f"Failed to get env value {key} from config: {e}")
            return local_value

    def _initialize_service(self):
        """Initialize Gmail API service."""
        try:
            credentials = self._get_credentials()

            from googleapiclient.discovery import build
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
            # Try to use provided access token
            credentials = Credentials(token=self.access_token)

            # Check if token is expired and refresh if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

                # Update access token if refreshed
                if credentials.token != self.access_token:
                    logger.info("Gmail token refreshed successfully")
                    self.access_token = credentials.token

            return credentials
        except Exception as e:
            raise AuthenticationError(f"Failed to get credentials: {e}")

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

    def delete_email(self, message_id: str, dry_run: bool = False):
        """
        Delete email from Gmail.

        Args:
            message_id: Gmail message ID
            dry_run: If True, log action without deleting (for debugging)
        """
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete email: {message_id}")
                return

            logger.info(f"Deleting email: {message_id}")

            self.service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()

            logger.info(f"Successfully deleted email: {message_id}")
        except Exception as e:
            raise DeletionError(f"Failed to delete email {message_id}: {e}")

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


class DeletionError(Exception):
    """Raised when email deletion fails."""
    pass

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    ch = GmailChecker()
    # mails = ch.search_emails(query="from:no-reply@strava.com")
    # print(mails)
    # m = ch._get_message(mails[0]['id'])
    # print(m)
    m = ch.search_strava_code_emails()
    print(m[0]['code'])

    # m = ch.search_strava_export_emails()
    # print(m[0]['download_url'])

