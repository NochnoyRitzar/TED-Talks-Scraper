import os

TED_URL = 'https://www.ted.com'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "upgrade-insecure-requests": "1"
}

LOG_FILE_NAME = 'scraping.log'

SCRAPED_CATALOG_PAGES_PATH = os.path.join('data', 'scraped_catalog_pages')
SCRAPED_TALK_PAGES_PATH = os.path.join('data', 'scraped_talk_pages')
