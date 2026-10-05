import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from config import (
    PUBMED_BASE_URL,
    PUBMED_SEARCH_QUERY,
    PUBMED_TARGET_DOCUMENTS,
)
from scripts.connectors.base import Document

def fetch_url(endpoint: str, params: dict[str, str]) -> bytes:
    query_string = urllib.parse.urlencode(params)
    url = f"{PUBMED_BASE_URL}/{endpoint}?{query_string}"

    with urllib.request.urlopen(url) as response:
        return response.read()


def search_pubmed(query: str, count: int) -> list[str]:
    xml_data = fetch_url(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": query,
            "retmax": str(count * 2),
            "retmode": "xml",
        },
    )

    root = ET.fromstring(xml_data)
    return [element.text for element in root.findall(".//Id") if element.text]


def fetch_articles(pubmed_ids: list[str]) -> bytes:
    return fetch_url(
        "efetch.fcgi",
        {
            "db": "pubmed",
            "id": ",".join(pubmed_ids),
            "retmode": "xml",
        },
    )


def extract_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    
    return " ".join("".join(element.itertext()).split())


def parse_articles(xml_data: bytes, limit: int) -> list[Document]:
    root = ET.fromstring(xml_data)
    documents: list[Document] = []

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", default = "").strip()
        title = extract_text(article.find(".//ArticleTitle"))

        abstract_parts = []
        for abstract_element in article.findall(".//Abstract/AbstractText"):
            text = extract_text(abstract_element)
            label = abstract_element.attrib.get("Label")
            if label and text:
                text = f"{label}: {text}"

            if text:
                abstract_parts.append(text)
        
        abstract = " ".join(abstract_parts)

        if not pmid or not title or not abstract:
            continue

        documents.append(
            {
                "id": pmid,
                "text": f"{title} {abstract}",
                "metadata": {
                    "source": "pubmed",
                    "title": title,
                    "abstract": abstract,
                }
            }
        )

        if len(documents) >= limit:
            break

    return documents


def fetch() -> list[Document]:
    pubmed_ids = search_pubmed(PUBMED_SEARCH_QUERY, PUBMED_TARGET_DOCUMENTS)
    xml_data = fetch_articles(pubmed_ids)
    return parse_articles(xml_data, PUBMED_TARGET_DOCUMENTS)

# def fetch_documents(query: str, limit: int) -> list[Document]:
#     pubmed_ids = search_pubmed(query, limit)
#     xml_data = fetch_articles(pubmed_ids)
#     return parse_articles(xml_data, limit)

