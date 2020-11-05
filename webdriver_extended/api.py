import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

LOGGER = logging.getLogger(__name__)

# JavaScript in Python; nice
CHROME_IS_HEADLESS_SCRIPT = "return navigator.plugins.length == 0"
CHROME_GET_FILES_SCRIPT = """a = document.querySelector('downloads-manager').shadowRoot.querySelectorAll('#mainContainer downloads-item');
b = [];
for (i = 0; i < a.length; i++) {
    c = a[i];
    try {
        p = c.shadowRoot.querySelector('#progress').value
    }
    catch (TypeError) {
        p = 100
    }
    b.push({"file_name" : c.content.querySelector('#file-link').text, "progress" : p});
}
return b;"""
CHROME_CLEAR_DOWNLOADS_SCRIPT = "document.querySelector('downloads-manager').shadowRoot.querySelector('#toolbar').shadowRoot.querySelector('#moreActionsMenu').querySelector('button.clear-all').click()"


class WebElementExtended(webdriver.remote.webelement.WebElement):
    # TODO: Seperate this out as necessary.

    def click_to_download(self, max_download_started_check_num=30):
        """Click on an element to download a file to the current directory

        Args:
            max_download_started_check_num (int, optional): Max number of times to check if a download started. Defaults to 30.

        Raises:
        Raises:
            FileNotFoundError: If the file never started downloading
            NotImplementedError: If you attempt to use this on anything besides ChromeExtended
        """
        driver = self._parent
        if isinstance(driver, ChromeExtended):
            if driver.headless:
                LOGGER.info("Headless, so using click_to_download_2")
                # Use older, more error-prone method, as unfortunately this only loads a blank page if headless
                return self.click_to_download_2()
            original_window = driver.current_window_handle
            try:
                download_dir_name = driver.download_dir_name
                Path(download_dir_name).mkdir(parents=True, exist_ok=True)
                # Wait for folder unlock
                while os.path.isfile(os.path.join(download_dir_name, ".lock")):
                    sleep(1)
                # Write lock file
                with open(os.path.join(download_dir_name, ".lock"), "w") as f:
                    f.write("")
                self.click()
                driver.new_tab(url="chrome://downloads")
                # Wait for one download to start
                download_started_check_num = 0
                downloading_files = []
                while not downloading_files:
                    download_started_check_num += 1
                    downloading_files = driver.execute_script(
                        CHROME_GET_FILES_SCRIPT)
                    if not downloading_files:
                        if download_started_check_num == max_download_started_check_num:
                            raise FileNotFoundError(
                                "Download never started")
                        else:
                            sleep(2)
                    else:
                        break
                # Poll until all downloads are done
                while True:
                    if all(f["progress"] == 100 for f in downloading_files):
                        break
                    else:
                        sleep(1)
                for f in downloading_files:
                    file_name = f["file_name"]
                    shutil.move(os.path.join(
                        download_dir_name, file_name), file_name)
                # Clear all
                driver.execute_script(CHROME_CLEAR_DOWNLOADS_SCRIPT)
            finally:
                driver.switch_to.window(original_window)
                driver.save_screenshot("a.png")
                try:
                    shutil.rmtree(download_dir_name)
                except FileNotFoundError:
                    pass
        else:
            # Not implemented yet for other browsers
            raise NotImplementedError

    def click_to_download_2(self, max_download_started_check_num=30):
        """Click on an element to download a file to the current directory. Uses a worse, more error-prone algorithm

        Args:
            max_download_started_check_num (int, optional): Max number of times to check if a download started. Defaults to 30.

        Raises:
            FileNotFoundError: If the file never started downloading
            NotImplementedError: If you attempt to use this on anything besides ChromeExtended
        """
        driver = self._parent
        if isinstance(driver, ChromeExtended):
            download_dir_name = driver.download_dir_name
            Path(download_dir_name).mkdir(parents=True, exist_ok=True)
            try:
                # Wait for folder unlock
                while os.path.isfile(os.path.join(download_dir_name, ".lock")):
                    sleep(1)
                # Write lock file
                with open(os.path.join(download_dir_name, ".lock"), "w") as f:
                    f.write("")
                self.click()
                download_started = False
                while True:
                    # Wait for download to start
                    download_started_check_num = 0
                    while not download_started:
                        download_started_check_num += 1
                        try:
                            if os.listdir(download_dir_name):
                                download_started = True
                            else:
                                raise FileNotFoundError(
                                    "Download never started")
                        except FileNotFoundError as e:
                            if download_started_check_num == max_download_started_check_num:
                                raise e
                            else:
                                sleep(2)
                    # If the download finished
                    files = os.listdir(download_dir_name)
                    files.remove(".lock")
                    try:
                        file_name = files[0]
                        if not file_name.endswith(".crdownload"):
                            break
                    except IndexError:
                        # Not there yet
                        pass
                    sleep(1)
                shutil.move(os.path.join(
                    download_dir_name, file_name), file_name)
            finally:
                try:
                    shutil.rmtree(download_dir_name)
                except FileNotFoundError:
                    pass
        else:
            # Not implemented yet for other browsers
            raise NotImplementedError


class ChromeExtended(webdriver.Chrome):
    """webdriver.Chrome, but with more stuff"""
    _web_element_cls = WebElementExtended

    def __init__(self, *args, **kwargs):
        self.download_dir_name = os.path.abspath(
            os.path.join(os.sep, "tmp", f".downloads-{uuid.uuid4()}"))
        options = kwargs.get("options", Options())
        prefs = options.experimental_options.get("prefs", {})
        prefs.update({"download.default_directory": self.download_dir_name})
        options.add_experimental_option("prefs", prefs)
        kwargs["options"] = options
        super().__init__(*args, **kwargs)

    @property
    def headless(self):
        return self.execute_script(CHROME_IS_HEADLESS_SCRIPT)

    def new_tab(self, url=None, switch_to=True):
        """Open a new tab

        Args:
            url (str, optional): The URL. If None, open a blank tab. Defaults to None.
            switch_to (bool, optional): If True, switch to the new tab. Defaults to True.
        """
        if url is None:
            url = ""
        original_window = self.current_window_handle
        self.execute_script("window.open('');")
        self.switch_to.window(self.window_handles[-1])
        self.get(url)
        if not switch_to:
            self.switch_to.window(original_window)
