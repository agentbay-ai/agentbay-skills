#!/usr/bin/env python3
"""
Web Scraper - Fetch web pages and save as HTML or Markdown (text + images).
Minimal dependencies: only requests and beautifulsoup4.
"""

import argparse
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser
import hashlib
from collections import deque
from typing import Set, Optional, Dict
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Error: Missing required package: {e}", file=sys.stderr)
    print("\nInstall dependencies:", file=sys.stderr)
    print("  pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


class RecursiveScraper:
    """Recursive web scraper with smart filtering and rate limiting."""

    def __init__(self, start_url: str, output_dir: Path, output_format: str,
                 max_depth: int = 2, max_pages: int = 50, same_domain: bool = True,
                 respect_robots: bool = True, rate_limit: float = 0.5,
                 download_images: bool = True, timeout: int = 30):
        self.start_url = start_url
        self.output_dir = output_dir
        self.output_format = output_format
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.same_domain = same_domain
        self.respect_robots = respect_robots
        self.rate_limit = rate_limit
        self.download_images = download_images
        self.timeout = timeout

        # State tracking
        self.visited: Set[str] = set()
        self.queue: deque = deque([(start_url, 0)])  # (url, depth)
        self.robots_cache: Dict[str, Optional[RobotFileParser]] = {}
        self.last_request_time: Dict[str, float] = {}
        self.stats = {'success': 0, 'failed': 0, 'skipped': 0}

        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Extract domain from start URL
        parsed = urlparse(start_url)
        self.start_domain = parsed.netloc
        self.base_scheme = parsed.scheme

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        url, _ = urldefrag(url)
        return url.rstrip('/')

    def is_valid_url(self, url: str, depth: int) -> bool:
        """Check if URL should be crawled."""
        url = self.normalize_url(url)

        if url in self.visited or len(self.visited) >= self.max_pages:
            return False

        if depth > self.max_depth:
            return False

        try:
            parsed = urlparse(url)
        except Exception:
            return False

        if not parsed.scheme or not parsed.netloc:
            return False

        if parsed.scheme not in ['http', 'https']:
            return False

        if self.same_domain and parsed.netloc != self.start_domain:
            return False

        # Skip non-content URLs
        skip_extensions = ['.pdf', '.zip', '.tar', '.gz', '.exe', '.dmg',
                           '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
                           '.css', '.js', '.xml', '.json']
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        return True

    def check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if not self.respect_robots:
            return True

        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        if robots_url not in self.robots_cache:
            try:
                resp = self.session.get(robots_url, timeout=5)
                if resp.status_code == 200:
                    rp = RobotFileParser()
                    rp.parse(resp.text.splitlines())
                    self.robots_cache[robots_url] = rp
                else:
                    self.robots_cache[robots_url] = None
            except Exception:
                self.robots_cache[robots_url] = None

        robots = self.robots_cache[robots_url]
        if robots is not None:
            return robots.can_fetch("*", url)
        return True

    def rate_limit_delay(self, domain: str):
        """Apply rate limiting per domain."""
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
        self.last_request_time[domain] = time.time()

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract all valid links from HTML."""
        links = set()
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            absolute_url = urljoin(base_url, href)
            normalized = self.normalize_url(absolute_url)
            if normalized:
                links.add(normalized)
        return links

    def get_output_path(self, url: str) -> Path:
        """Generate output file path from URL."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        if not path_parts:
            filename = 'index'
        else:
            filename = path_parts[-1]
            # Remove query string from filename
            filename = re.sub(r'[?#].*$', '', filename)
            if len(path_parts) > 1:
                subdir = self.output_dir / '/'.join(path_parts[:-1])
                subdir.mkdir(parents=True, exist_ok=True)
                return subdir / f"{filename}.{self.output_format}"

        return self.output_dir / f"{filename}.{self.output_format}"

    def scrape_page(self, url: str, depth: int):
        """Scrape a single page."""
        try:
            domain = urlparse(url).netloc
            self.rate_limit_delay(domain)

            if not self.check_robots_txt(url):
                self.stats['skipped'] += 1
                return

            # Fetch page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            html_content = response.text

            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract links for next depth
            if depth < self.max_depth:
                links = self.extract_links(soup, url)
                for link in links:
                    if self.is_valid_url(link, depth + 1):
                        self.queue.append((link, depth + 1))

            # Save page
            output_path = self.get_output_path(url)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if self.output_format == 'html':
                self.save_html(soup, url, output_path)
            else:  # markdown
                self.save_markdown(soup, url, output_path)

            self.stats['success'] += 1

        except Exception as e:
            print(f"Failed to scrape {url}: {e}", file=sys.stderr)
            self.stats['failed'] += 1

    def save_html(self, soup: BeautifulSoup, url: str, output_path: Path):
        """Save HTML with downloaded images."""
        if self.download_images:
            images_dir = self.output_dir / "images"
            images_dir.mkdir(exist_ok=True)

            for img_tag in soup.find_all('img'):
                src = img_tag.get('src') or img_tag.get('data-src')
                if src:
                    local_path = self.download_image(src, url, images_dir)
                    if local_path:
                        img_tag['src'] = local_path

        # Add metadata
        meta_tag = soup.new_tag('meta', attrs={'name': 'scraper-source', 'content': url})
        if soup.head:
            soup.head.append(meta_tag)

        output_path.write_text(str(soup), encoding='utf-8')

    def save_markdown(self, soup: BeautifulSoup, url: str, output_path: Path):
        """Save as Markdown with downloaded images."""
        if self.download_images:
            images_dir = self.output_dir / "images"
            images_dir.mkdir(exist_ok=True)

            for img_tag in soup.find_all('img'):
                src = img_tag.get('src') or img_tag.get('data-src')
                if src:
                    local_path = self.download_image(src, url, images_dir)
                    if local_path:
                        img_tag['src'] = local_path

        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # Convert to markdown (simple conversion)
        markdown = self.html_to_markdown(soup)

        # Add metadata header
        title = soup.title.string if soup.title else 'Web Page'
        header = f"# {title}\n\n"
        header += f"Source: {url}\n"
        header += f"Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        header += "---\n\n"

        output_path.write_text(header + markdown, encoding='utf-8')

    def html_to_markdown(self, soup: BeautifulSoup) -> str:
        """Simple HTML to Markdown conversion."""
        lines = []

        # Get main content (try common content containers)
        content = soup.find('main') or soup.find('article') or soup.find('body') or soup

        for element in content.descendants:
            if element.name == 'h1':
                lines.append(f"\n# {element.get_text().strip()}\n")
            elif element.name == 'h2':
                lines.append(f"\n## {element.get_text().strip()}\n")
            elif element.name == 'h3':
                lines.append(f"\n### {element.get_text().strip()}\n")
            elif element.name == 'h4':
                lines.append(f"\n#### {element.get_text().strip()}\n")
            elif element.name == 'h5':
                lines.append(f"\n##### {element.get_text().strip()}\n")
            elif element.name == 'h6':
                lines.append(f"\n###### {element.get_text().strip()}\n")
            elif element.name == 'p':
                text = element.get_text().strip()
                if text:
                    lines.append(f"\n{text}\n")
            elif element.name == 'a':
                text = element.get_text().strip()
                href = element.get('href', '')
                if text and href:
                    lines.append(f"[{text}]({href})")
            elif element.name == 'img':
                src = element.get('src', '')
                alt = element.get('alt', 'image')
                if src:
                    lines.append(f"\n![{alt}]({src})\n")
            elif element.name == 'code':
                lines.append(f"`{element.get_text()}`")
            elif element.name == 'pre':
                code_text = element.get_text().strip()
                lines.append(f"\n```\n{code_text}\n```\n")
            elif element.name == 'li':
                text = element.get_text().strip()
                if text and element.parent.name in ['ul', 'ol']:
                    prefix = '- ' if element.parent.name == 'ul' else '1. '
                    lines.append(f"{prefix}{text}\n")

        return ''.join(lines)

    def download_image(self, img_url: str, base_url: str, images_dir: Path) -> Optional[str]:
        """Download an image and return relative path."""
        try:
            absolute_url = urljoin(base_url, img_url)
            url_hash = hashlib.md5(absolute_url.encode()).hexdigest()[:12]

            parsed = urlparse(absolute_url)
            ext = Path(parsed.path).suffix
            if not ext or len(ext) > 5:
                ext = '.jpg'

            filename = f"{url_hash}{ext}"
            local_path = images_dir / filename

            if not local_path.exists():
                response = self.session.get(absolute_url, timeout=10, stream=True)
                response.raise_for_status()

                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

            return f"images/{filename}"

        except Exception as e:
            print(f"Failed to download image {img_url}: {e}", file=sys.stderr)
            return None

    def run(self):
        """Run the recursive scraper."""
        print(f"Starting recursive scrape from {self.start_url}", file=sys.stderr)
        print(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}", file=sys.stderr)
        print(f"Output directory: {self.output_dir}", file=sys.stderr)

        processed = 0
        while self.queue and len(self.visited) < self.max_pages:
            url, depth = self.queue.popleft()

            url = self.normalize_url(url)
            if not self.is_valid_url(url, depth):
                continue

            self.visited.add(url)
            processed += 1
            print(f"[{processed}/{self.max_pages}] Scraping: {url}", file=sys.stderr)
            self.scrape_page(url, depth)

        print(f"\n✓ Scraping complete!", file=sys.stderr)
        print(f"  Success: {self.stats['success']}", file=sys.stderr)
        print(f"  Failed: {self.stats['failed']}", file=sys.stderr)
        print(f"  Skipped (robots.txt): {self.stats['skipped']}", file=sys.stderr)
        print(f"  Output: {self.output_dir}", file=sys.stderr)


def sanitize_filename(url: str) -> str:
    """Generate a safe filename from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/").replace("/", "-")

    name = f"{domain}-{path}" if path else domain
    name = re.sub(r'[^\w\-\.]', '-', name)
    name = re.sub(r'-+', '-', name).strip('-')

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{name}-{timestamp}"


def scrape_single_page(url: str, output_path: Path, output_format: str,
                      download_images: bool = True, timeout: int = 30) -> None:
    """Scrape a single URL and save to file."""
    print(f"Fetching {url} ...", file=sys.stderr)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        # Download images if enabled
        if download_images:
            images_dir = output_path.parent / "images"
            images_dir.mkdir(exist_ok=True)

            print(f"Downloading images to {images_dir} ...", file=sys.stderr)
            img_count = 0
            for img_tag in soup.find_all('img'):
                src = img_tag.get('src') or img_tag.get('data-src')
                if src:
                    absolute_url = urljoin(url, src)
                    try:
                        url_hash = hashlib.md5(absolute_url.encode()).hexdigest()[:12]
                        ext = Path(urlparse(absolute_url).path).suffix or '.jpg'
                        if len(ext) > 5:
                            ext = '.jpg'

                        filename = f"{url_hash}{ext}"
                        local_path = images_dir / filename

                        if not local_path.exists():
                            img_resp = session.get(absolute_url, timeout=10, stream=True)
                            img_resp.raise_for_status()
                            with open(local_path, 'wb') as f:
                                for chunk in img_resp.iter_content(chunk_size=8192):
                                    f.write(chunk)

                        img_tag['src'] = f"images/{filename}"
                        img_count += 1
                    except Exception as e:
                        print(f"Failed to download {src}: {e}", file=sys.stderr)

            print(f"Downloaded {img_count} images", file=sys.stderr)

        # Save based on format
        if output_format == 'html':
            # Add metadata
            meta_tag = soup.new_tag('meta', attrs={'name': 'scraper-source', 'content': url})
            if soup.head:
                soup.head.append(meta_tag)

            print(f"Saving HTML to {output_path} ...", file=sys.stderr)
            output_path.write_text(str(soup), encoding='utf-8')

        else:  # markdown
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()

            # Simple markdown conversion
            markdown = html_to_markdown(soup)

            # Add metadata header
            title = soup.title.string if soup.title else 'Web Page'
            header = f"# {title}\n\n"
            header += f"Source: {url}\n"
            header += f"Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            header += "---\n\n"

            print(f"Saving Markdown to {output_path} ...", file=sys.stderr)
            output_path.write_text(header + markdown, encoding='utf-8')

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def html_to_markdown(soup: BeautifulSoup) -> str:
    """Simple HTML to Markdown conversion."""
    lines = []
    content = soup.find('main') or soup.find('article') or soup.find('body') or soup

    for element in content.descendants:
        if isinstance(element, str):
            continue

        if element.name == 'h1':
            lines.append(f"\n# {element.get_text().strip()}\n")
        elif element.name == 'h2':
            lines.append(f"\n## {element.get_text().strip()}\n")
        elif element.name == 'h3':
            lines.append(f"\n### {element.get_text().strip()}\n")
        elif element.name == 'h4':
            lines.append(f"\n#### {element.get_text().strip()}\n")
        elif element.name == 'h5':
            lines.append(f"\n##### {element.get_text().strip()}\n")
        elif element.name == 'h6':
            lines.append(f"\n###### {element.get_text().strip()}\n")
        elif element.name == 'p':
            text = element.get_text().strip()
            if text:
                lines.append(f"\n{text}\n")
        elif element.name == 'a' and element.parent.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']:
            text = element.get_text().strip()
            href = element.get('href', '')
            if text and href:
                lines.append(f"[{text}]({href})")
        elif element.name == 'img':
            src = element.get('src', '')
            alt = element.get('alt', 'image')
            if src:
                lines.append(f"\n![{alt}]({src})\n")
        elif element.name == 'code' and element.parent.name != 'pre':
            lines.append(f"`{element.get_text()}`")
        elif element.name == 'pre':
            code_text = element.get_text().strip()
            lines.append(f"\n```\n{code_text}\n```\n")
        elif element.name == 'li':
            text = ' '.join(element.stripped_strings)
            if text and element.parent and element.parent.name in ['ul', 'ol']:
                prefix = '- ' if element.parent.name == 'ul' else '1. '
                lines.append(f"{prefix}{text}\n")

    return ''.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape web pages and save as HTML or Markdown (with text and images)"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL to scrape"
    )
    parser.add_argument(
        "--format",
        choices=["html", "md", "markdown"],
        default="html",
        help="Output format (default: html)"
    )
    parser.add_argument(
        "--output",
        help="Output file path (auto-generated if not specified)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--no-download-images",
        action="store_true",
        help="Don't download images (keep URLs only)"
    )

    # Recursive scraping options
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Enable recursive scraping (follow links)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum recursion depth (default: 2)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum number of pages to scrape (default: 50)"
    )
    parser.add_argument(
        "--same-domain",
        action="store_true",
        default=True,
        help="Only follow links within the same domain (default: True)"
    )
    parser.add_argument(
        "--no-respect-robots",
        action="store_true",
        help="Ignore robots.txt (use with caution)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.5,
        help="Minimum seconds between requests to same domain (default: 0.5)"
    )

    args = parser.parse_args()

    # Normalize format
    output_format = "md" if args.format == "markdown" else args.format

    # Recursive scraping mode
    if args.recursive:
        if args.output:
            output_dir = Path(args.output).expanduser().resolve()
        else:
            base_name = sanitize_filename(args.url)
            output_dir = Path.cwd() / f"{base_name}-recursive"

        output_dir.mkdir(parents=True, exist_ok=True)

        scraper = RecursiveScraper(
            start_url=args.url,
            output_dir=output_dir,
            output_format=output_format,
            max_depth=args.max_depth,
            max_pages=args.max_pages,
            same_domain=args.same_domain,
            respect_robots=not args.no_respect_robots,
            rate_limit=args.rate_limit,
            download_images=not args.no_download_images,
            timeout=args.timeout
        )

        scraper.run()
        print(str(output_dir))  # Output directory to stdout
        return

    # Single page mode
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        base_name = sanitize_filename(args.url)
        output_path = Path.cwd() / f"{base_name}.{output_format}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    scrape_single_page(
        args.url,
        output_path,
        output_format,
        download_images=not args.no_download_images,
        timeout=args.timeout
    )

    print(f"\n✓ Saved to: {output_path}", file=sys.stderr)
    print(str(output_path))  # Output path to stdout


if __name__ == "__main__":
    main()
