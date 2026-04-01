import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
import time

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

# Domains to skip during scraping
SKIP_DOMAINS = [
    'google.com', 'youtube.com', 'facebook.com',
    'twitter.com', 'instagram.com', 'linkedin.com',
    'amazon.com', 'wikipedia.org',
]


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return (
            parsed.scheme in ('http', 'https') and
            bool(parsed.netloc) and
            not any(skip in domain for skip in SKIP_DOMAINS)
        )
    except Exception:
        return False


def scrape_url(url: str, timeout: int = 10) -> dict:
    """
    Visit a URL and return clean readable text + page title.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Get page title
        title = ''
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Remove junk tags
        for tag in soup(['script', 'style', 'nav', 'footer',
                         'header', 'aside', 'form', 'iframe',
                         'noscript', 'ads', 'advertisement']):
            tag.decompose()

        # Try to find the main article content
        main_content = (
            soup.find('article') or
            soup.find('main') or
            soup.find('div', class_=lambda c: c and 'content' in c.lower()) or
            soup.find('div', class_=lambda c: c and 'article' in c.lower()) or
            soup.body
        )

        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)

        # Clean up excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text).strip()

        return {
            'url': url,
            'title': title,
            'text': text[:8000],  # limit to 8000 chars
            'success': True,
        }

    except requests.exceptions.Timeout:
        return {'url': url, 'title': '', 'text': '', 'success': False, 'error': 'Timeout'}
    except requests.exceptions.ConnectionError:
        return {'url': url, 'title': '', 'text': '', 'success': False, 'error': 'Connection error'}
    except Exception as e:
        return {'url': url, 'title': '', 'text': '', 'success': False, 'error': str(e)}


def search_google(query: str, num_results: int = 5) -> list:
    """
    Search Google and return a list of result URLs.
    """
    encoded_query = quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results + 3}"

    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')

        urls = []

        # Extract URLs from Google results
        for a_tag in soup.select('a[href]'):
            href = a_tag.get('href', '')

            # Google wraps URLs in /url?q=...
            if href.startswith('/url?q='):
                url = href.split('/url?q=')[1].split('&')[0]
                if is_valid_url(url) and url not in urls:
                    urls.append(url)

            if len(urls) >= num_results:
                break

        return urls

    except Exception as e:
        print(f"Google search failed: {e}")
        return []


def scrape_sources(query: str, num_results: int = 5) -> list:
    """
    Full pipeline:
    1. Search Google for the query
    2. Scrape each result URL
    3. Return list of {url, title, text}
    """
    urls = search_google(query, num_results)

    if not urls:
        return []

    sources = []
    for url in urls:
        result = scrape_url(url)
        if result['success'] and len(result['text']) > 100:
            sources.append(result)
        time.sleep(0.5)  # polite delay between requests

    return sources