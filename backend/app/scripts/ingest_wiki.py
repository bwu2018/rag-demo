#!/usr/bin/env python3
"""
Ingest Coppermind Wiki XML export into vector database.
"""

import os
import sys
from pathlib import Path

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.services.wiki_ingestion import CoppermindWikiIngestion


def main():
    print("=" * 60)
    print("Coppermind Wiki XML Ingestion")
    print("=" * 60)

    # Look for XML file
    xml_path = Path("./data/coppermind.xml")

    if not xml_path.exists():
        print(f"\n❌ XML file not found: {xml_path}")
        print("\nPlease ensure you have:")
        print("1. Downloaded the wiki XML using export_wiki.py")
        print("2. Placed coppermind.xml in backend/data/")
        return

    print(f"\nFound XML file: {xml_path}")
    print(f"File size: {xml_path.stat().st_size / (1024 * 1024):.2f} MB")

    # Initialize ingestion service
    print("\nInitializing ingestion service...")
    ingestion = CoppermindWikiIngestion(persist_directory="./data/chromadb")

    # Ingest from XML
    print("\nStarting ingestion...")
    print("This may take several minutes...\n")

    total_chunks = ingestion.ingest_from_xml(str(xml_path))

    print("\n" + "=" * 60)
    print(f"✅ Successfully ingested {total_chunks} chunks")
    print("=" * 60)


if __name__ == "__main__":
    main()
