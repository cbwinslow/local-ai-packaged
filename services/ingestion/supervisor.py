"""
GovInfo Document Ingestion Supervisor

Orchestrates the ingestion process for government documents from the govinfo_download_queue.
Manages batch processing, error handling, and status updates.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import aiofiles
import os
import time
from dataclasses import dataclass

from .download_processor import DocumentDownloader
from .text_extractor import TextExtractor
from .entity_processor import EntityProcessor
from .embedding_generator import EmbeddingGenerator
from ..db.connection import get_db_connection
from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Statistics for document processing."""
    total_processed: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0
    extraction_errors: int = 0
    entity_processing_errors: int = 0
    embedding_errors: int = 0
    total_time_seconds: float = 0.0

class IngestionSupervisor:
    """Supervisor for government document ingestion pipeline."""

    def __init__(
        self,
        max_concurrent_downloads: int = 5,
        max_workers: int = 10,
        batch_size: int = 50,
        temp_dir: str = "/tmp/govinfo_downloads"
    ):
        """
        Initialize the supervisor.

        Args:
            max_concurrent_downloads: Maximum concurrent downloads
            max_workers: Maximum thread workers for processing
            batch_size: Number of documents to process in each batch
            temp_dir: Temporary directory for downloads
        """
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)

        # Initialize processors
        self.downloader = DocumentDownloader(
            temp_dir=str(self.temp_dir),
            max_concurrent=self.max_concurrent_downloads
        )
        self.extractor = TextExtractor()
        self.entity_processor = EntityProcessor()
        self.embedding_generator = EmbeddingGenerator()

        # Thread pool for CPU-bound processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_ingestion_loop(self, poll_interval: int = 30) -> None:
        """
        Run continuous ingestion loop checking for new documents.

        Args:
            poll_interval: Seconds to wait between polls
        """
        logger.info("Starting government document ingestion loop")

        while True:
            try:
                stats = await self.process_batch()
                if stats.total_processed > 0:
                    logger.info(f"Processed {stats.total_processed} documents in batch")
                else:
                    logger.info("No documents to process, sleeping...")

                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.error(f"Ingestion loop error: {e}")
                await asyncio.sleep(10)  # Brief pause on error

    async def process_batch(self) -> ProcessingStats:
        """
        Process a batch of documents from the queue.

        Returns:
            ProcessingStats: Statistics of the processing run
        """
        stats = ProcessingStats()
        start_time = time.time()

        try:
            # Get pending documents from queue
            queue_items = await self._get_pending_documents(self.batch_size)
            if not queue_items:
                stats.total_time_seconds = time.time() - start_time
                return stats

            stats.total_processed = len(queue_items)

            # Process documents in parallel
            tasks = []
            for item in queue_items:
                task = asyncio.create_task(self._process_single_document(item, stats))
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # Update queue statuses
            await self._update_batch_statuses(queue_items)

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
        finally:
            stats.total_time_seconds = time.time() - start_time

        return stats

    async def _process_single_document(self, item: Dict[str, Any], stats: ProcessingStats) -> None:
        """
        Process a single document through the full pipeline.

        Args:
            item: Queue item with package_id, package_link, etc.
            stats: Stats to update
        """
        package_id = item['package_id']

        try:
            # Step 1: Download document
            download_result = await self.downloader.download_document(item)
            if not download_result.get('file_path'):
                logger.error(f"Failed to download {package_id}")
                stats.failed_downloads += 1
                return

            stats.successful_downloads += 1
            file_path = download_result['file_path']

            # Step 2: Extract text
            try:
                extracted_text = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.extractor.extract_text, file_path
                )

                # Store extracted content in database
                await self._store_extracted_content(package_id, extracted_text)

                logger.info(f"Extracted {len(extracted_text)} chars from {package_id}")

            except Exception as e:
                logger.error(f"Text extraction failed for {package_id}: {e}")
                stats.extraction_errors += 1
                return

            # Step 3: Process entities (run in thread pool)
            try:
                entities = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.entity_processor.extract_entities, extracted_text
                )

                # Store entities in database and graph
                await self._store_entities(package_id, entities)
                await self._store_entity_graph(entities, item)

            except Exception as e:
                logger.error(f"Entity processing failed for {package_id}: {e}")
                stats.entity_processing_errors += 1

            # Step 4: Generate embeddings (run in thread pool)
            try:
                embeddings = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.embedding_generator.generate_embeddings, extracted_text
                )

                # Store embeddings in vector database
                await self._store_embeddings(package_id, embeddings, extracted_text)

            except Exception as e:
                logger.error(f"Embedding generation failed for {package_id}: {e}")
                stats.embedding_errors += 1

        except Exception as e:
            logger.error(f"Processing failed for {package_id}: {e}")
        finally:
            # Cleanup temporary file
            if 'file_path' in locals():
                await self._cleanup_file(file_path)

    async def _get_pending_documents(self, limit: int) -> List[Dict[str, Any]]:
        """
        Get pending documents from the download queue.

        Args:
            limit: Maximum number of documents to fetch

        Returns:
            List of queue items
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor(cursor_factory=RealDictCursor) as cur:
                await cur.execute("""
                    SELECT dq.id, dq.package_id, gp.package_link, gp.collection_id,
                           gp.title, gp.doc_class, gp.pages, gp.last_modified
                    FROM govinfo_download_queue dq
                    JOIN govinfo_packages gp ON dq.package_id = gp.package_id
                    WHERE dq.status = 'pending'
                    ORDER BY dq.priority DESC, dq.created_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                """, (limit,))

                return [dict(row) for row in await cur.fetchall()]
        finally:
            await conn.close()

    async def _update_batch_statuses(self, queue_items: List[Dict[str, Any]]) -> None:
        """
        Update status of processed queue items.

        Args:
            queue_items: List of processed items
        """
        if not queue_items:
            return

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                package_ids = [item['package_id'] for item in queue_items]
                await cur.execute("""
                    UPDATE govinfo_download_queue
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE package_id = ANY(%s)
                """, (package_ids,))

                await conn.commit()
        finally:
            await conn.close()

    async def _store_extracted_content(self, package_id: str, content: str) -> None:
        """
        Store extracted content in database.

        Args:
            package_id: GovInfo package ID
            content: Extracted text content
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE govinfo_packages
                    SET content = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE package_id = %s
                """, (content, package_id))

                await conn.commit()
        finally:
            await conn.close()

    async def _store_entities(self, package_id: str, entities: List[Dict[str, Any]]) -> None:
        """
        Store entities in database.

        Args:
            package_id: GovInfo package ID
            entities: Extracted entities
        """
        # Implementation depends on entity schema
        # Store in govinfo_entities table or similar
        pass

    async def _store_entity_graph(self, entities: List[Dict[str, Any]], item: Dict[str, Any]) -> None:
        """
        Store entity relationships in Neo4j graph.

        Args:
            entities: Extracted entities
            item: Queue item with document info
        """
        # Implementation for Neo4j integration
        # Create nodes and relationships
        pass

    async def _store_embeddings(self, package_id: str, embeddings: List[float], text: str) -> None:
        """
        Store embeddings in vector database.

        Args:
            package_id: GovInfo package ID
            embeddings: Generated embeddings
            text: Original text
        """
        # Implementation for Qdrant/AlfaDB integration
        # Store vectors with metadata
        pass

    async def _cleanup_file(self, file_path: str) -> None:
        """
        Clean up temporary download file.

        Args:
            file_path: Path to file to remove
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")


async def main():
    """Main function for running ingestion supervisor."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    supervisor = IngestionSupervisor()

    # Run ingestion loop
    await supervisor.run_ingestion_loop()


if __name__ == "__main__":
    asyncio.run(main())
