from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache

def create_session():
    session = requests_cache.CachedSession(
        backend="redis",
        cache_name="httpcache",
        expire_after=60 * 60 * 24 * 7,
        allowable_methods=("GET", "POST"),
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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.5993.70 Safari/537.36"
        }
    )

    return session

session = create_session()
