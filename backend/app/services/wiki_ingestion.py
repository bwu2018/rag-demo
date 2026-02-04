import re
import xml.etree.ElementTree as ET
from typing import List

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class CoppermindWikiIngestion:
    def __init__(self, persist_directory: str = "./data/chromadb"):
        self.persist_directory = persist_directory

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Initialize vector store
        self.vectorstore = Chroma(
            collection_name="cosmere_wiki",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )

    def clean_wiki_markup(self, text: str) -> str:
        """Remove common wiki markup patterns"""
        if not text:
            return ""

        # Remove templates like {{template}}
        text = re.sub(r"\{\{[^}]+\}\}", "", text)

        # Remove file/image references
        text = re.sub(r"\[\[File:[^\]]+\]\]", "", text)
        text = re.sub(r"\[\[Image:[^\]]+\]\]", "", text)

        # Convert wiki links [[link|text]] to just text
        text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
        text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

        # Remove references <ref>...</ref>
        text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
        text = re.sub(r"<ref[^>]*\/>", "", text)

        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Remove category tags
        text = re.sub(r"\[\[Category:[^\]]+\]\]", "", text)

        # Remove == headers == but keep the text
        text = re.sub(r"={2,}([^=]+)={2,}", r"\1", text)

        # Clean up whitespace
        text = re.sub(r"\n\n+", "\n\n", text)
        text = text.strip()

        return text

    def parse_mediawiki_xml(self, xml_file: str) -> List[Document]:
        """Parse MediaWiki XML export file"""
        print(f"Parsing XML file: {xml_file}")

        # MediaWiki namespace
        ns = {"mw": "http://www.mediawiki.org/xml/export-0.11/"}

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return []

        documents = []

        # Find all pages
        pages = root.findall("mw:page", ns)
        print(f"Found {len(pages)} pages in XML")

        for i, page in enumerate(pages):
            try:
                # Get title
                title_elem = page.find("mw:title", ns)
                if title_elem is None:
                    continue
                title = title_elem.text

                # Skip redirect pages
                redirect = page.find("mw:redirect", ns)
                if redirect is not None:
                    continue

                # Get page ID
                id_elem = page.find("mw:id", ns)
                page_id = id_elem.text if id_elem is not None else "unknown"

                # Get latest revision content
                revision = page.find("mw:revision", ns)
                if revision is None:
                    continue

                text_elem = revision.find("mw:text", ns)
                if text_elem is None or text_elem.text is None:
                    continue

                content = text_elem.text

                # Clean wiki markup
                clean_content = self.clean_wiki_markup(content)

                # Skip very short pages
                if len(clean_content) < 100:
                    continue

                # Create document
                doc = Document(
                    page_content=clean_content,
                    metadata={
                        "title": title,
                        "page_id": page_id,
                        "source": f"https://coppermind.net/wiki/{title.replace(' ', '_')}",
                    },
                )

                documents.append(doc)

                if (i + 1) % 100 == 0:
                    print(
                        f"Processed {i + 1}/{len(pages)} pages... ({len(documents)} valid)"
                    )

            except Exception as e:
                print(f"Error processing page: {e}")
                continue

        print(f"\nSuccessfully parsed {len(documents)} pages")
        return documents

    def ingest_from_xml(self, xml_file: str):
        """Main ingestion pipeline from XML file"""
        # Parse XML
        documents = self.parse_mediawiki_xml(xml_file)

        if not documents:
            print("No valid documents found!")
            return 0

        # Split documents into chunks
        print("\nSplitting documents into chunks...")
        all_splits = self.text_splitter.split_documents(documents)
        print(f"Created {len(all_splits)} chunks")

        # Add to vector store in batches
        print("\nAdding to vector store...")
        batch_size = 100
        for i in range(0, len(all_splits), batch_size):
            batch = all_splits[i : i + batch_size]
            self.vectorstore.add_documents(batch)
            print(
                f"Added batch {i // batch_size + 1}/{(len(all_splits) - 1) // batch_size + 1}"
            )

        print("\n✅ Ingestion complete!")
        return len(all_splits)
