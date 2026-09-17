# Code Improvements TODO

## High Priority

### Unused Imports
- [x] Remove unused import in `src/google/gmail.py`:
  - Line 7: `from email.policy import default as email_policy` - removed
  - Line 12: `from email.message import EmailMessage` - removed
  - Line 19: `from google_auth.oauthlib.flow import InstalledAppFlow` - removed

### Unused Exception Classes
- [x] Remove unused exception class in `src/google/gmail.py`:
  - Line 571: `class TokenExpiredError(Exception)` - removed

## Medium Priority

### Code Style Improvements
- [x] Refactor generic exception handling in `src/google/gmail.py`:
  - Lines 292-296 and 348-353 - extracted to helper method `_get_message_body()`
  - Consolidated duplicate base64 decode error handling
  - Lines 292-291, 346-348, 383-385 - generic exception handling patterns preserved

### Type Hints Cleanup
- [x] Clean up unused type hints in `src/google/gmail.py`:
  - Line 11: `from typing import List, Dict, Optional, Tuple` - Tuple removed
  - EmailMessage type hints in docstrings - preserved for documentation

### Code Duplication
- [x] Extract common error handling patterns in `src/google/gmail.py`:
  - Created `_get_message_body()` helper method to handle base64 decoding
  - Eliminated duplicate try-except blocks for message body extraction

### Import Organization
- [x] Organize imports in `src/google/gmail.py`:
  - Standard library imports at top (base64, re, os, logging, requests, yaml)
  - Google API imports after standard library
  - Type hints imports last

## Low Priority

### Consistency Improvements
- [x] Review and potentially remove commented code:
  - Lines 598-600: Removed commented search_emails code
  - Lines 605-606: Removed commented search_strava_export_emails code

## Logging Improvements

### Centralized Logging Configuration
- [x] Create centralized logging configuration module (`src/logging_config.py`):
  - Setup logging with configurable levels
  - Rotating file handler with size limits (10MB, 5 backups)
  - Console and file output options
  - Module-specific logger configuration
  - Decorator for function execution logging
  - Convenience logging functions

### Print Statement Replacement
- [ ] Replace print() statements with logging in `src/google/gmail.py`:
  - Line 598: `print(m[0]['code'])` → `logger.info()`
  - Remove `logging.basicConfig()` (replaced by centralized config)

- [ ] Replace print() statements with logging in `src/google/spreadsheet.py`:
  - Line 36: Error fetching existing IDs
  - Line 59: No new activities message
  - Line 108: Headers written message
  - Line 138: Error appending activities
  - Line 142: Successfully appended message

- [ ] Replace print() statements with logging in `src/download_account.py`:
  - Lines 51-135: Multiple print statements for workflow execution
  - Use appropriate log levels (INFO for workflow steps, ERROR for failures)
  - Keep error messages but use logger.error()
  - Consider using structured logging for configuration display

- [ ] Replace print() statements with logging in `src/main.py`:
  - Line 26: Spreadsheet append message
  - Line 72: Unhandled exception message
  - Use INFO for success, ERROR for exceptions

### Logging Best Practices
- [ ] Configure log levels via environment variable:
  - Support `LOG_LEVEL` environment variable
  - Default to INFO level

- [ ] Add log rotation configuration:
  - Automatic rotation at 10MB
  - Keep 5 backup files
  - Configure log file path

- [ ] Implement module-specific loggers:
  - `google.gmail` - GmailChecker class
  - `google.spreadsheet` - Spreadsheet functions
  - `strava.browser_automation` - Browser automation
  - `strava.browser_config` - Browser configuration
  - `download_account` - Account download workflow
  - `main` - Cloud function entry point

## Summary of Improvements

### Completed Tasks
- Removed 3 unused imports (email_policy, EmailMessage, InstalledAppFlow)
- Removed 1 unused exception class (TokenExpiredError)
- Cleaned up unused type hint (Tuple)
- Extracted duplicate code to helper method `_get_message_body()`
- Removed commented out code
- Improved code organization
- Created centralized logging configuration

### Logging Implementation Plan
**Benefits:**
- Consistent log formatting across all modules
- Structured and searchable logs
- Automatic rotation prevents disk space issues
- Configurable log levels via environment
- Professional logging practices

**Implementation Priority:**
1. Create centralized logging (done)
2. Replace print statements in all files (pending)
3. Configure log levels and rotation (pending)

**Estimated Impact:**
- ~30 print statements to be replaced
- Consistent error tracking with stack traces
- Better debugging and monitoring capabilities
- Production-ready logging configuration
