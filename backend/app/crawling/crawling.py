"""Discover page URLs published through a website's XML sitemaps.

Run from the ``backend`` directory:

    python -m app.core.crawling https://example.com
"""

import gzip
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

BANKS_WEBSITES = {"ING":"https://www.ing.be",
                  "KBC":"https://www.kbc.be",
                  "Belfius":"https://www.belfius.be",
                  "BNP":"https://www.bnpparibasfortis.be",
                  "Revolut":"https://www.revolut.com",
                  "Argenta":"https://www.argenta.be",
                  "Crelan":"https://www.crelan.be",
                  "Beobank":"https://www.beobank.be"
                 }
BANKS_SITEMAPS = {"ING":["https://www.ing.be/sitemap-cms.xml"],
                  "KBC":[""],
                  "Belfius":["https://www.belfius.be/sitemap.xml"],
                  "BNP":["https://www.bnpparibasfortis.be/sitemap.xml"],
                  "Revolut":["https://www.revolut.com/sitemap-index-0.xml"],
                  "Argenta":["https://www.argenta.be/fr.sitemap.xml"],
                  "Crelan":["https://www.crelan.be/sitemap.xml"],
                  "Beobank":["https://www.beobank.be/fr/sitemap.xml"]}
USER_AGENT = "SitemapUrlCrawler/1.0"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
BANK_URLS_FILE = Path(__file__).resolve().parents[2] / "data" / "bank_urls.json"


def _robots_url(website_url: str) -> str:
    parsed = urlsplit(website_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("website_url must be an absolute HTTP(S) URL")
    return urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))


def _download(url: str, timeout: float, retries: int) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:  # nosec B310: caller supplies URL
                body = response.read()
                content_encoding = response.headers.get("Content-Encoding", "").lower()
            break
        except HTTPError as exc:
            if exc.code not in RETRYABLE_STATUS_CODES or attempt == retries:
                raise RuntimeError(f"Could not download {url}: HTTP {exc.code}") from exc
        except (URLError, OSError) as exc:
            if attempt == retries:
                raise RuntimeError(f"Could not download {url}: {exc}") from exc
        time.sleep(2**attempt)

    if url.lower().split("?", 1)[0].endswith(".gz") or content_encoding == "gzip":
        try:
            return gzip.decompress(body)
        except OSError as exc:
            raise RuntimeError(f"Could not decompress sitemap {url}: {exc}") from exc
    return body


def sitemap_urls_from_robots(website_url: str, *, timeout = 30, retries = 3) -> list[str]:
    """Return the sitemap URLs declared by the site's ``robots.txt`` file."""
    robots_url = _robots_url(website_url)
    robots = _download(robots_url, timeout, retries).decode("utf-8", errors="replace")
    sitemap_urls: list[str] = []
    for line in robots.splitlines():
        name, separator, value = line.partition(":")
        if separator and name.strip().lower() == "sitemap" and value.strip():
            sitemap_urls.append(urljoin(robots_url, value.strip()))
    return sitemap_urls


def _fallback_sitemaps(website_url: str) -> list[str]:
    """Return configured sitemap URLs whose host matches ``website_url``."""
    requested_host = urlsplit(website_url).netloc.lower().removeprefix("www.")
    fallback_urls: list[str] = []
    for sitemap_urls in BANKS_SITEMAPS.values():
        for sitemap_url in sitemap_urls:
            if not sitemap_url:
                continue
            sitemap_host = urlsplit(sitemap_url).netloc.lower().removeprefix("www.")
            if sitemap_host == requested_host and sitemap_url not in fallback_urls:
                fallback_urls.append(sitemap_url)
    return fallback_urls


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _locations(xml: bytes, sitemap_url: str) -> tuple[bool, list[str]]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise RuntimeError(f"Invalid XML in sitemap {sitemap_url}: {exc}") from exc

    is_index = _local_name(root) == "sitemapindex"
    expected_entry = "sitemap" if is_index else "url"
    locations: list[str] = []
    for entry in root:
        if _local_name(entry) != expected_entry:
            continue
        for child in entry:
            if _local_name(child) == "loc" and child.text and child.text.strip():
                locations.append(urljoin(sitemap_url, child.text.strip()))
                break
    return is_index, locations


def crawl_sitemap_urls(website_url: str, *, timeout = 30, retries = 2) -> list[str]:
    """Return all page URLs in sitemaps declared in ``website_url``'s robots.txt.

    Sitemap indexes are followed recursively. URLs are returned in their sitemap
    order, with duplicates removed. If robots.txt or one of its sitemap files
    cannot be downloaded, matching sitemap URLs from ``BANKS_SITEMAPS`` are
    tried as a fallback.
    """
    if retries < 0:
        raise ValueError("retries must be zero or greater")
    try:
        pending = sitemap_urls_from_robots(website_url, timeout=timeout, retries=retries)
    except RuntimeError:
        pending = _fallback_sitemaps(website_url)
        if not pending:
            raise
    visited_sitemaps: set[str] = set()
    seen_pages: set[str] = set()
    pages: list[str] = []
    last_download_error: RuntimeError | None = None

    while pending:
        sitemap_url = pending.pop(0)
        if sitemap_url in visited_sitemaps:
            continue
        visited_sitemaps.add(sitemap_url)
        try:
            sitemap_xml = _download(sitemap_url, timeout, retries)
        except RuntimeError as exc:
            last_download_error = exc
            for fallback_url in _fallback_sitemaps(website_url):
                if fallback_url not in visited_sitemaps and fallback_url not in pending:
                    pending.append(fallback_url)
            continue

        is_index, locations = _locations(sitemap_xml, sitemap_url)
        if is_index:
            pending.extend(locations)
        else:
            for page_url in locations:
                if page_url not in seen_pages:
                    seen_pages.add(page_url)
                    pages.append(page_url)
    if not pages and last_download_error:
        raise last_download_error
    return pages


def crawl_banks_url(output_file: Path = BANK_URLS_FILE) -> Path:
    """Crawl bank sitemaps and save their page URLs as JSON.

    Returns the path of the generated JSON file. Banks that cannot be crawled
    are reported and omitted from the file.
    """
    bank_pages = {}
    for bank, bank_url in BANKS_WEBSITES.items():
        try:
            print(f"Crawl pages of bank {bank} :")
            bank_pages[bank] = crawl_sitemap_urls(bank_url)
            print(f"Found {len(bank_pages[bank])} urls.")
        except RuntimeError as exc:
            print(f"{bank}: could not crawl {bank_url}: {exc}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(bank_pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Printed results in output file {output_file}.")
    return output_file


def main() -> None:
    output_file = crawl_banks_url()
    print(f"Saved crawled bank URLs to {output_file}")

if __name__ == "__main__":
    main()
