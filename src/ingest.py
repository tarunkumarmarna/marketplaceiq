"""
Reads the 12 docs from data/raw using source_manifest.csv for metadata,
chunks them, embeds them, and pushes everything into Qdrant.
Run this once - it's not part of the live query path.
"""

import csv
import pdfplumber
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
from dotenv import load_dotenv

from config import (
    DATA_RAW_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP,
    QDRANT_COLLECTION_NAME,
)

load_dotenv()


def load_manifest():
    # manifest gives us area/company/tier/sources per file - way more
    # reliable than trying to parse all that out of the filename
    manifest_path = DATA_RAW_DIR / "source_manifest.csv"
    rows = {}
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows[row["filename"]] = row
    return rows


def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # always grab plain text first, so any prose around a table
            # doesn't get lost - the old version only kept text when a
            # page had no detected table at all
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

            # then look for genuine tables and add a cleaned version below
            tables = page.extract_tables()
            for table in tables:
                clean_rows = []
                for row in table:
                    clean_cells = [cell.strip() if cell else "" for cell in row]
                    non_empty = sum(1 for c in clean_cells if c)
                    # a real content row (Category / Window / Type) has at
                    # least 2 filled cells - mostly-empty rows are usually
                    # pdfplumber false-positives on nav bars/page headers,
                    # not real table data
                    if non_empty >= 2:
                        clean_rows.append(clean_cells)

                # only trust this as a genuine table if it produced
                # multiple populated rows - one stray row is more likely
                # noise than an actual data table
                if len(clean_rows) >= 2:
                    for row in clean_rows:
                        text += " | ".join(c for c in row if c) + "\n"
    return text

def chunk_text(text, chunk_size, overlap):
    # simple sliding window - step forward by (chunk_size - overlap) each time
    # so consecutive chunks share some text and we don't lose meaning at the cut
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def main():
    manifest = load_manifest()
    embedder = SentenceTransformer(EMBEDDING_MODEL)

    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=60,  # default timeout is too short for free-tier cluster + batch uploads
    )

    # (re)create the collection fresh each run - this script is meant to be
    # re-runnable from scratch, not appended to every time
    if client.collection_exists(QDRANT_COLLECTION_NAME):
       client.delete_collection(QDRANT_COLLECTION_NAME)

    client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),

        # 384 = output dimension of all-MiniLM-L6-v2, check this if the
        # embedding model in config.py ever changes
    )

    point_id = 0
    points = []

    for filename, meta in manifest.items():
        pdf_path = DATA_RAW_DIR / filename
        if not pdf_path.exists():
            print(f"⚠️ Skipping {filename} - not found in data/raw")
            continue

        text = extract_text(pdf_path)
        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"{filename}: {len(chunks)} chunks")

        vectors = embedder.encode(chunks)

        for chunk, vector in zip(chunks, vectors):
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                     payload={
                        "page_content": chunk,
                        "metadata": {
                            "filename": filename,
                            "area": meta["area"],
                            "company": meta["company"],
                            "source_tier": meta["source_tier"],
                            "primary_source": meta["primary_source"],
                            "has_tables": meta["has_tables"],
                        },
                    },
                )
            )
            point_id += 1

    # upload in batches instead of one giant request - a single huge upsert
    # can time out on the network before Qdrant finishes writing it
    batch_size = 20
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=batch)
        print(f"  uploaded batch {i // batch_size + 1} ({len(batch)} points)")

    print(f"\n✅ Done. {point_id} total chunks stored in Qdrant.")

if __name__ == "__main__":
    main()