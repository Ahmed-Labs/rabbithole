import os
from urllib.parse import urlparse

import requests_cache
from redis import Redis
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session():
    redis_url = os.getenv("REDIS_CACHE_URL")
    if not redis_url:
        raise RuntimeError("REDIS_CACHE_URL is not set")

    parsed = urlparse(redis_url)
    redis_host = parsed.hostname or "localhost"
    redis_port = parsed.port or 6379
    redis_db = int(parsed.path.lstrip("/")) if parsed.path else 0

    session = requests_cache.CachedSession(
        backend="redis",
        namespace="httpcache",
        expire_after=60 * 60 * 24 * 7,
        allowable_methods=("GET", "POST"),
        connection=Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=False,
        ),
    )

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/118.0.5993.70 Safari/537.36"
            )
        }
    )

    return session


class _SessionProxy:
    _session = None

    def _get(self):
        if self._session is None:
            self._session = create_session()
        return self._session

    def __getattr__(self, name):
        return getattr(self._get(), name)


session = _SessionProxy()
