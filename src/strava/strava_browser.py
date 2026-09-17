import logging
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from strava.browser_automation import BrowserAutomation
from strava.browser_automation import (
    BrowserAutomationError,
    CookieConsentError,
    ElementNotFoundError,
    VerificationError,
    LoginError
)


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
        if not browser.driver:
            raise RuntimeError("browser didn't provide valid driver object")
        self.driver = browser.driver
        self.config = browser.config
        self.logger.info("StravaBrowser initialized")

    def dismiss_cookie_consent(self) -> bool:
        """
        Dismiss cookie consent modal if present.

        Raises:
            CookieConsentError: If consent cannot be dismissed
        """
        try:
            self.logger.info("Checking for cookie consent modal")

            # Try to find and click the decline button
            decline_button = self.browser.get_element(By.ID, "CybotCookiebotDialogBodyButtonDecline", timeout=3)
            if decline_button:
                decline_button.click()
                self.logger.info("Cookie consent modal dismissed")
                # time.sleep(2)
                return True
            else:
                self.logger.info("No cookie consent modal found")
                return False

        except CookieConsentError:
            raise
        except Exception as e:
            self.logger.warning(f"Error dismissing cookie consent: {e}")
            return False


    def _code_is_sent(self):
        success_text = "We sent you a code"
        try:
            WebDriverWait(self.driver, 5).until(
                EC.text_to_be_present_in_element((By.XPATH, "//body"), success_text)
            )
            self.logger.info("Verification code already sent")
            return True
        except TimeoutException:
            self.logger.info("No code verification visible")
            return False

    def initiate_login(self, email: str) -> bool:
        """
        Login to Strava using email.

        Args:
            email: Email address

        Returns:
            True if initiate_login successful, False otherwise

        Raises:
            LoginError: If email field not found after retries
            ElementNotFoundError: If submit button not clickable after retries
        """
        try:
            self.logger.info("Starting Strava initiate_login")

            # Navigate to initiate_login page
            self.driver.get("https://www.strava.com/login")
            # time.sleep(2)

            # Dismiss cookie consent modal
            self.dismiss_cookie_consent()

            retry = 4

            while not self._code_is_sent() and retry:
                # Find and input email
                email_field = self.browser.get_element(By.ID, "mobile-email")
                if email_field:
                    email_field.clear()
                    email_field.send_keys(email)
                    self.logger.info("Email entered")
                else:
                    self.logger.error("Email field not found")
                    continue

                # Submit form
                # time.sleep(7)
                try:
                    submit_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                    )
                    submit_button.click()
                    self.logger.info("Login form submitted successfully")
                    time.sleep(5)
                except TimeoutException:
                    self.logger.error("Submit button not clickable after waiting")
                    continue

                # Wait for redirect
                retry -= 1

            if not self._code_is_sent():
                raise LoginError("Code not sent after retry attempts")

            return True

        except LoginError:
            raise
        except Exception as e:
            self.logger.error(f"Strava initiate_login failed: {e}")
            return False

    def finalize_login(self, otp: str) -> bool:
        """
        Finalize login by entering OTP code.

        Finds the only input with type 'number' on the page, inserts the OTP code,
        and submits using the "Next" button.

        Args:
            otp: OTP verification code

        Returns:
            True if login finalized successfully, False otherwise

        Raises:
            ElementNotFoundError: If OTP input field not found
            LoginError: If OTP code cannot be entered or submitted
        """
        try:
            self.logger.info("Starting finalize_login with OTP")

            # Wait for OTP input field to appear
            try:
                otp_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='number']"))
                )
            except TimeoutException:
                self.logger.error("OTP input field not found")
                raise ElementNotFoundError(By.XPATH, "//input[@type='number']")

            # Clear any existing content
            otp_input.clear()

            # Insert OTP code
            otp_input.send_keys(otp)
            self.logger.info(f"OTP code entered: {otp}")

            # Wait for "Next" button to appear
            try:
                next_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Next']"))
                )
            except TimeoutException:
                self.logger.error("Next button not found")
                return False

            # Click the Next button
            next_button.click()
            self.logger.info("Next button clicked")

            # Wait for redirect or login success
            time.sleep(3)

            return True

        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"finalize_login failed: {e}")
            return False

    def navigate_to_download_account(self) -> bool:
        """
        Navigate to download_my_account page.

        Returns:
            True if navigation successful, False otherwise

        Raises:
            VerificationError: If navigation to download page fails
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
                raise VerificationError(f"Failed to navigate to download_my_account page. URL: {current_url}")

        except VerificationError:
            raise
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    def trigger_archive_request(self) -> bool:
        """
        Click the request-archive button.

        Returns:
            True if button clicked successfully, False otherwise

        Raises:
            ElementNotFoundError: If button not found
            VerificationError: If button cannot be clicked
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
                raise VerificationError("Failed to click archive request button")

        except VerificationError:
            raise
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Archive request failed: {e}")
            return False

    def verify_success_message(self) -> bool:
        """
        Verify success message appears.

        Returns:
            True if success message found, False otherwise

        Raises:
            VerificationError: If success message not found
        """
        try:
            self.logger.info("Verifying success message")

            # Expected success message
            success_text = "Request received"

            # Wait for success message
            success = self.browser.verify_success_message(success_text)

            if success:
                self.logger.info("Archive request confirmed")
                return True
            else:
                self.logger.warning("Success message not found")
                raise VerificationError(f"Success message '{success_text}' not found")

        except VerificationError:
            raise
        except Exception as e:
            self.logger.error(f"Success message verification failed: {e}")
            return False

    def request_extract(self) -> bool:
        """
        Navigate to download_my_account, click archive button, and verify success.

        Returns:
            True if extraction request completed successfully, False otherwise

        Raises:
            VerificationError: If navigation, button click, or verification fails
        """
        try:
            self.logger.info("Starting archive request extraction")

            # Step 1: Navigate to download_my_account
            if not self.navigate_to_download_account():
                self.logger.error("Navigation failed")
                raise VerificationError("Navigation to download page failed")

            # Step 2: Click archive button
            if not self.trigger_archive_request():
                self.logger.error("Archive button click failed")
                raise VerificationError("Archive button click failed")

            # Step 3: Verify success
            if not self.verify_success_message():
                self.logger.warning("Success message verification failed")
                # This is not critical for the workflow

            self.logger.info("Archive request extraction completed")
            return True

        except VerificationError:
            raise
        except Exception as e:
            self.logger.error(f"Archive request extraction failed: {e}")
            return False

        except Exception as e:
            self.logger.error(f"Archive request extraction failed: {e}")
            return False
