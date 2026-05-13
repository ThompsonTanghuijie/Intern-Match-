import logging
import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import get_settings
from app.models import Source
from app.services.parser import parse_github_markdown_jobs

logger = logging.getLogger(__name__)


@dataclass
class CrawlFetchResult:
    status_code: int
    text: str | None
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False


class GitHubMarkdownCrawler:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.trust_env = False
        retry = Retry(
            total=self.settings.request_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update(
            {
                "User-Agent": self.settings.github_user_agent,
                "Accept": "text/markdown,text/plain,*/*",
            }
        )

    def fetch(self, source: Source) -> CrawlFetchResult:
        headers: dict[str, str] = {}
        if source.etag:
            headers["If-None-Match"] = source.etag
        if source.last_modified:
            headers["If-Modified-Since"] = source.last_modified
        time.sleep(max(self.settings.request_rate_limit_seconds, 0))
        response = self.session.get(
            source.url,
            headers=headers,
            timeout=self.settings.request_timeout_seconds,
        )
        if response.status_code == 304:
            return CrawlFetchResult(status_code=304, text=None, not_modified=True)
        response.raise_for_status()
        return CrawlFetchResult(
            status_code=response.status_code,
            text=response.text,
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
        )

    def crawl(self, source: Source):
        fetched = self.fetch(source)
        if fetched.not_modified or not fetched.text:
            return fetched, []
        jobs = parse_github_markdown_jobs(fetched.text, source.url)
        logger.info("parsed %s jobs from %s", len(jobs), source.name)
        return fetched, jobs
