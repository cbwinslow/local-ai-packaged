"""
Document Download Processor

Handles downloading government documents from GovInfo links with rate limiting,
error handling, and retry logic.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import aiohttp
import aiofiles
from urllib.parse import urlparse
import time
import hashlib
from functools import wraps

from ..config import settings

logger = logging.getLogger(__name__)


def rate_limited(calls_per_minute: int):
    """Decorator to rate limit function calls."""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class DocumentDownloader:
    """Handles downloading of government documents with robust error handling."""

    def __init__(
        self,
        temp_dir: str = "/tmp/govinfo_downloads",
        max_concurrent: int = 5,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_rpm: int = 60,
        user_agent: str = "GovInfo-Ingestion/1.0"
    ):
        """
        Initialize the downloader.

        Args:
            temp_dir: Directory for temporary downloads
            max_concurrent: Maximum concurrent downloads
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit_rpm: Rate limit in requests per minute
            user_agent: HTTP User-Agent header
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.rate_limit_rpm = rate_limit_rpm
        self.user_agent = user_agent

        # Semaphore for limiting concurrent downloads
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Session will be initialized per task
        self.session = None

    async def __aenter__(self):
        """Async context manager enter."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={'User-Agent': self.user_agent}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def download_document(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download a single document from the queue item.

        Args:
            item: Queue item with package_link, package_id, etc.

        Returns:
            Dict with download result including file_path, content_length, etc.
        """
        package_id = item['package_id']
        package_link = item['package_link']

        async with self.semaphore:
            return await self._download_with_retry(package_id, package_link)

    @rate_limited(rate_limit_rpm=60)
    async def _download_with_retry(self, package_id: str, package_link: str) -> Dict[str, Any]:
        """
        Download document with retry logic.

        Args:
            package_id: GovInfo package ID
            package_link: Download URL

        Returns:
            Dict with download result
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession(
                        timeout=self.timeout,
                        headers={'User-Agent': self.user_agent}
                    )

                async with self.session.get(package_link) as response:
                    if response.status != 200:
                        error_msg = f"HTTP {response.status}: {response.reason}"
                        logger.warning(f"Download attempt {attempt + 1} failed for {package_id}: {error_msg}")
                        last_error = Exception(error_msg)
                        continue

                    # Generate unique filename
                    url_hash = hashlib.md5(package_link.encode()).hexdigest()[:8]
                    filename = f"{package_id}_{url_hash}"
                    file_path = self.temp_dir / filename

                    # Get file extension from URL or content-type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'pdf' in content_type:
                        file_path = file_path.with_suffix('.pdf')
                    elif 'xml' in content_type:
                        file_path = file_path.with_suffix('.xml')
                    elif 'html' in content_type or 'text' in content_type:
                        file_path = file_path.with_suffix('.html')

                    # Download file
                    content_length = 0
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            content_length += len(chunk)

                    logger.info(f"Downloaded {package_id}: {content_length} bytes")
                    return {
                        'file_path': str(file_path),
                        'content_length': content_length,
                        'content_type': content_type,
                        'url': package_link
                    }

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {package_id}: {e}")
                last_error = e

                # Exponential backoff with jitter
                backoff = min(2 ** attempt, 30)  # Max 30 seconds
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(backoff)

        # All attempts failed
        logger.error(f"All download attempts failed for {package_id}: {last_error}")
        return {'error': str(last_error) if last_error else 'Unknown error'}

    async def download_batch(self, items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Download multiple documents concurrently.

        Args:
            items: List of queue items

        Returns:
            List of download results
        """
        tasks = [self.download_document(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a downloaded file.

        Args:
            file_path: Path to the file

        Returns:
            Dict with file information or None if file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            return None

        stat = path.stat()
        return {
            'file_path': str(path),
            'file_size': stat.st_size,
            'modified_time': stat.st_mtime,
            'exists': True
        }


# Standalone usage
async def main():
    """Test the downloader."""
    async with DocumentDownloader() as downloader:
        # Example usage
        test_item = {
            'package_id': 'USCODE-2019-title42',
            'package_link': 'https://www.govinfo.gov/content/pkg/USCODE-2019-title42/pdf/USCODE-2019-title42.pdf'
        }

        result = await downloader.download_document(test_item)
        print("Download result:", result)


if __name__ == "__main__":
    asyncio.run(main())
