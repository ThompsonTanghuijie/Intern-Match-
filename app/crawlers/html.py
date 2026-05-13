import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import get_settings


class HtmlCrawler:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.trust_env = False
        retry = Retry(
            total=self.settings.request_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update({"User-Agent": self.settings.github_user_agent})

    def fetch_soup(self, url: str) -> BeautifulSoup:
        time.sleep(max(self.settings.request_rate_limit_seconds, 0))
        response = self.session.get(url, timeout=self.settings.request_timeout_seconds)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
