import os
import uuid

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .webelement import WebElement

# JavaScript in Python; nice
IS_HEADLESS_SCRIPT = "return navigator.plugins.length == 0"


class WebDriver(webdriver.Chrome):
    """webdriver.Chrome, but with more stuff"""
    _web_element_cls = WebElement

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
        return self.execute_script(IS_HEADLESS_SCRIPT)

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
