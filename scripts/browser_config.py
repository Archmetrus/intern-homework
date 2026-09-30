"""Browser selection without a distribution-specific executable path."""
import os
import shutil
from pathlib import Path


def configure_browser(options):
    requested = os.environ.get('CHROME_PATH')
    if requested:
        executable = shutil.which(str(Path(requested).expanduser()))
        if not executable:
            raise ValueError('CHROME_PATH executable not found')
        options.binary_location = executable
        return
    for candidate in ('google-chrome-stable', 'google-chrome', 'chromium', 'chromium-browser'):
        executable = shutil.which(candidate)
        if executable:
            options.binary_location = executable
            return
    # Leave unset so Selenium Manager can locate installed browsers on Windows/macOS.
