import logging
import time
from typing import Optional, Any, Dict
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys
from pathlib import Path


class BrowserAutomation:
    """Core browser automation module for Strava archive requests."""

    def __init__(self, config: dict):
        """
        Initialize browser automation with configuration.

        Args:
            config: Dictionary containing browser configuration
        """
        self.config = config
        self.driver = None
        self.logger = self._setup_logger()
        self.logger.info("BrowserAutomation initialized")

    def _setup_logger(self) -> logging.Logger:
        """Set up logger for browser automation."""
        logger = logging.getLogger("BrowserAutomation")
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        # File handler
        file_handler = logging.FileHandler('browser_automation.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def initialize_browser(self) -> webdriver.Firefox:
        """
        Initialize Firefox WebDriver with configuration.

        Returns:
            Firefox WebDriver instance
        """
        try:
            headless = self.config.get('headless', False)
            verbose = self.config.get('verbose', True)

            options = Options()
            options.headless = headless
            options.add_argument("--disable-infobars")
            options.add_argument("--start-maximized")
            options.add_argument("--window-size=1920,1080")

            if verbose:
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--enable-logging")

            # Use absolute Firefox binary path for snap installation
            firefox_binary = self.config.get('firefox_binary')
            if firefox_binary:
                options.binary_location = firefox_binary
                self.logger.info(f"Using Firefox binary: {firefox_binary}")

            self.logger.info(f"Initializing Firefox WebDriver (headless={headless})")

            self.driver = webdriver.Firefox(options=options)
            self.logger.info("Firefox WebDriver initialized successfully")
            return self.driver

        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise

    def cleanup(self):
        """Clean up browser session."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser session closed")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")

    def manual_pause(self, timeout: int = 10):
        """
        Pause for manual inspection.

        Args:
            timeout: Seconds to pause
        """
        if self.config.get('pause_on_action', True):
            self.logger.info(f"Pausing for manual inspection ({timeout} seconds)")
            print(f"\nPress Enter to continue after manual inspection...")
            input()
            self.logger.info("Manual inspection complete")

    def get_element(self, by: str, value: str, timeout: int = None) -> Optional:
        """
        Wait for and get element.

        Args:
            by: By locator strategy (e.g., 'ID', 'CSS_SELECTOR')
            value: Locator value
            timeout: Timeout in seconds

        Returns:
            WebElement if found, None otherwise
        """
        try:
            if timeout is None:
                timeout = self.config.get('timeout', 30)

            wait = WebDriverWait(self.driver, timeout)
            locator = getattr(By, by.upper(), By.CSS_SELECTOR)
            element = wait.until(EC.presence_of_element_located((locator, value)))
            return element

        except TimeoutException:
            self.logger.warning(f"Element not found with locator: {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting element: {e}")
            return None

    def click_element(self, by: str, value: str, timeout: int = None) -> bool:
        """
        Click element after waiting for it to be clickable.

        Args:
            by: By locator strategy
            value: Locator value
            timeout: Timeout in seconds

        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            element = self.get_element(by, value, timeout)
            if element:
                self.manual_pause(timeout=self.config.get('manual_pause_timeout', 10))
                element.click()
                self.logger.info(f"Clicked element: {by}={value}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error clicking element: {e}")
            return False

    def verify_success_message(self, success_text: str, timeout: int = None) -> bool:
        """
        Verify success message appears.

        Args:
            success_text: Expected success message text
            timeout: Timeout in seconds

        Returns:
            True if success message found, False otherwise
        """
        try:
            if timeout is None:
                timeout = self.config.get('timeout', 30)

            wait = WebDriverWait(self.driver, timeout)
            success_element = wait.until(EC.visibility_of_element_located((By.XPATH, f"//*[contains(text(), '{success_text}')]")))
            self.logger.info(f"Success message verified: {success_text}")
            return True

        except TimeoutException:
            self.logger.warning(f"Success message not found: {success_text}")
            return False
        except Exception as e:
            self.logger.error(f"Error verifying success message: {e}")
            return False

    def run(self):
        """
        Run the browser automation workflow.

        Returns:
            Success status
        """
        try:
            self.driver = self.initialize_browser()
            return True

        except Exception as e:
            self.logger.error(f"Browser automation failed: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
