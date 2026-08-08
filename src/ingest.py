"""
Reads the docs in data/raw using source_manifest.csv for metadata, pulls out
real table content properly (not just mangled plain text), chunks everything,
embeds it, and pushes it into Qdrant. This is a one-time offline step, not
part of the live query path - run it whenever the data corpus changes.
"""

import csv
import os

import pdfplumber
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_RAW_DIR,
    EMBEDDING_MODEL,
    QDRANT_COLLECTION_NAME,
)

load_dotenv()


def load_manifest():
    # manifest gives me area/company/tier/source per file directly - way more
    # reliable than trying to reverse-engineer that from the filename
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
            # plain text first, on every page - a page with a table can still
            # have real prose around it, don't want to lose that
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

            # then pull out genuine tables, filtering out near-empty rows -
            # pdfplumber sometimes mistakes a page's nav bar for a table,
            # and those rows are mostly empty cells, unlike a real data row
            for table in page.extract_tables():
                clean_rows = []
                for row in table:
                    cells = [c.strip() if c else "" for c in row]
                    if sum(1 for c in cells if c) >= 2:
                        clean_rows.append(cells)
                if len(clean_rows) >= 2:
                    for row in clean_rows:
                        text += " | ".join(c for c in row if c) + "\n"
    return text


def chunk_text(text, chunk_size, overlap):
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
        url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=60
    )

    if client.collection_exists(QDRANT_COLLECTION_NAME):
        client.delete_collection(QDRANT_COLLECTION_NAME)
    client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    point_id = 0
    points = []

    for filename, meta in manifest.items():
        pdf_path = DATA_RAW_DIR / filename
        if not pdf_path.exists():
            print(f"Skipping {filename} - not found in data/raw")
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
                        },
                    },
                )
            )
            point_id += 1

    # upload in batches - one giant request can time out on a free-tier cluster
    batch_size = 20
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME, points=points[i : i + batch_size]
        )

    print(f"\nDone. {point_id} total chunks stored in Qdrant.")


if __name__ == "__main__":
    main()
