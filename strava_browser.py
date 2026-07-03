import logging
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from browser_automation import BrowserAutomation


class StravaBrowser:
    """Strava-specific browser interactions for archive requests."""

    def __init__(self, browser: BrowserAutomation):
        """
        Initialize Strava browser automation.

        Args:
            browser: BrowserAutomation instance
        """
        self.browser = browser
        self.logger = self.browser.logger
        self.driver = browser.driver
        self.config = browser.config
        self.logger.info("StravaBrowser initialized")

    def dismiss_cookie_consent(self) -> bool:
        """
        Dismiss cookie consent modal if present.

        Returns:
            True if consent dismissed, False if not present
        """
        try:
            self.logger.info("Checking for cookie consent modal")

            # Try to find and click the decline button
            decline_button = self.get_element(By.ID, "CybotCookiebotDialogBodyButtonDecline", timeout=3)
            if decline_button:
                decline_button.click()
                self.logger.info("Cookie consent modal dismissed")
                # time.sleep(2)
                return True
            else:
                self.logger.info("No cookie consent modal found")
                return False

        except Exception as e:
            self.logger.warning(f"Error dismissing cookie consent: {e}")
            return False

    def login(self, email: str, password: str) -> bool:
        """
        Login to Strava using email.

        Args:
            email: Email address
            password: Password

        Returns:
            True if login successful, False otherwise
        """
        try:
            self.logger.info("Starting Strava login")

            # Navigate to login page
            self.driver.get("https://www.strava.com/login")
            # time.sleep(2)

            # Dismiss cookie consent modal
            self.dismiss_cookie_consent()

            retry = 4

            while not ("dashboard" in self.driver.current_url or "athlete" in self.driver.current_url) and retry:
                # Find and input email
                email_field = self.get_element(By.ID, "mobile-email")
                if email_field:
                    email_field.clear()
                    email_field.send_keys(email)
                    self.logger.info("Email entered")
                else:
                    self.logger.error("Email field not found")
                    return False

                # Find and input password
                # password_field = self.get_element(By.ID, "password")
                # if password_field:
                    # password_field.clear()
                    # password_field.send_keys(password)
                    # self.logger.info("Password entered")
                # else:
                    # self.logger.error("Password field not found")
                    # return False

                # Submit form
                time.sleep(7)
                try:
                    submit_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                    )
                    submit_button.click()
                    self.logger.info("Login form submitted successfully")
                    time.sleep(5)
                except TimeoutException:
                    self.logger.error("Submit button not clickable after waiting")
                    return False

                # Wait for redirect
                time.sleep(3)
                retry -= 1

                #TODO - verify a code screen (by finding element for email or code
                #TODO - if none can be found, still check if already redirected to dashboard

            # Verify login success
            if "dashboard" in self.driver.current_url or "athlete" in self.driver.current_url:
                self.logger.info("Strava login successful")
                return True
            else:
                self.logger.info("Not logged in properly")
                return False

        except Exception as e:
            self.logger.error(f"Strava login failed: {e}")
            return False

    def navigate_to_download_account(self) -> bool:
        """
        Navigate to download_my_account page.

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            self.logger.info("Navigating to download_my_account page")
            self.driver.get("https://www.strava.com/athlete/download_my_account")
            time.sleep(2)

            # Check if page loaded
            current_url = self.driver.current_url
            if "download_my_account" in current_url:
                self.logger.info("Successfully navigated to download_my_account page")
                return True
            else:
                self.logger.warning(f"Navigation may not have completed. URL: {current_url}")
                return False

        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    def trigger_archive_request(self) -> bool:
        """
        Click the request-archive button.

        Returns:
            True if button clicked successfully, False otherwise
        """
        try:
            self.logger.info("Clicking request-archive button")

            # Click the button
            success = self.browser.click_element(By.ID, "request-archive")

            if success:
                self.logger.info("Archive request button clicked successfully")
                time.sleep(2)
                return True
            else:
                self.logger.error("Failed to click archive request button")
                return False

        except Exception as e:
            self.logger.error(f"Archive request failed: {e}")
            return False

    def verify_success_message(self) -> bool:
        """
        Verify success message appears.

        Returns:
            True if success message found, False otherwise
        """
        try:
            self.logger.info("Verifying success message")

            # Expected success message
            success_text = "Archive request submitted successfully"

            # Wait for success message
            success = self.browser.verify_success_message(success_text)

            if success:
                self.logger.info("Archive request confirmed")
                return True
            else:
                self.logger.warning("Success message not found")
                return False

        except Exception as e:
            self.logger.error(f"Success message verification failed: {e}")
            return False

    def run_workflow(self, email: str, password: str) -> bool:
        """
        Run the complete archive request workflow.

        Args:
            email: Email address
            password: Password

        Returns:
            True if workflow completed successfully, False otherwise
        """
        try:
            self.logger.info("Starting archive request workflow")

            # Step 1: Login
            if not self.login(email, password):
                self.logger.error(f"Login failed")
                return False

            # Step 2: Navigate to download_my_account
            if not self.navigate_to_download_account():
                self.logger.error("Navigation failed")
                return False

            # Step 3: Click archive button
            if not self.trigger_archive_request():
                self.logger.error("Archive button click failed")
                return False

            # Step 4: Verify success
            if not self.verify_success_message():
                self.logger.warning("Success message verification failed")
                # This is not critical for the workflow

            self.logger.info("Archive request workflow completed")
            return True

        except Exception as e:
            self.logger.error(f"Archive request workflow failed: {e}")
            return False

    def get_element(self, by: str, value: str, timeout: int = None) -> Optional:
        """
        Get element using browser automation.

        Args:
            by: By locator strategy
            value: Locator value
            timeout: Timeout in seconds

        Returns:
            WebElement if found, None otherwise
        """
        return self.browser.get_element(by, value, timeout)
