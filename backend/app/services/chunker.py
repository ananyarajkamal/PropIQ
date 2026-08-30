"""Modular text chunking service for PropIQ.

Splits page-extracted proposal text into paragraph and sentence-boundary aware
chunks while maintaining complete evidence traceability to vendor name, document,
and page range.
"""

from typing import List
from app.models import PageExtractedText, ChunkMetadata


def chunk_document_pages(
    vendor_name: str,
    source_filename: str,
    vendor_index: int,
    pages: List[PageExtractedText],
    target_chunk_size: int = 800,
    overlap: int = 100,
) -> List[ChunkMetadata]:
    """Chunk page-extracted text while preserving complete evidence traceability.

    Args:
        vendor_name: Name of the vendor.
        source_filename: Original filename of the document.
        vendor_index: 1-based index of the vendor in the current analysis session.
        pages: List of PageExtractedText instances.
        target_chunk_size: Desired target character length per chunk (default 800).
        overlap: Character overlap between consecutive chunks (default 100).

    Returns:
        List of ChunkMetadata items.
    """
    chunks: List[ChunkMetadata] = []
    chunk_counter = 1

    for page in pages:
        if not page.text or not page.text.strip():
            continue

        raw_paras = [p.strip() for p in page.text.split("\n\n") if p.strip()]
        if not raw_paras:
            continue

        current_paras = []
        current_len = 0

        for para in raw_paras:
            para_len = len(para)

            if current_len + para_len > target_chunk_size and current_paras:
                chunk_text = "\n\n".join(current_paras)
                chunk_id = f"v{vendor_index:02d}_p{page.page_number:03d}_c{chunk_counter:03d}"

                chunks.append(
                    ChunkMetadata(
                        chunk_id=chunk_id,
                        vendor_name=vendor_name,
                        source_filename=source_filename,
                        start_page=page.page_number,
                        end_page=page.page_number,
                        character_count=len(chunk_text),
                        text=chunk_text,
                    )
                )
                chunk_counter += 1
                current_paras = [para]
                current_len = para_len
            else:
                current_paras.append(para)
                current_len += para_len + 2

        if current_paras:
            chunk_text = "\n\n".join(current_paras)
            chunk_id = f"v{vendor_index:02d}_p{page.page_number:03d}_c{chunk_counter:03d}"

            chunks.append(
                ChunkMetadata(
                    chunk_id=chunk_id,
                    vendor_name=vendor_name,
                    source_filename=source_filename,
                    start_page=page.page_number,
                    end_page=page.page_number,
                    character_count=len(chunk_text),
                    text=chunk_text,
                )
            )
            chunk_counter += 1

    return chunks
