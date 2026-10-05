from pathlib import Path

# Project directory containing this config.py file.
PROJECT_ROOT = Path(__file__).resolve().parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"


#Active Connector
ACTIVE_SOURCE = "pubmed"

#Generic Pipeline Outputs
DOCUMENTS_PATH = DATA_DIR / f"{ACTIVE_SOURCE}_documents.jsonl"
INDEX_PATH = DATA_DIR / f"{ACTIVE_SOURCE}.index"
METADATA_PATH = DATA_DIR / f"{ACTIVE_SOURCE}_metadata.json"
DATABASE_PATH = DATA_DIR / f"{ACTIVE_SOURCE}.db"

#PubMed Connector Settings

PUBMED_BASE_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
)
PUBMED_SEARCH_QUERY = "heart disease"
PUBMED_TARGET_DOCUMENTS = 50

#Embedding and Search
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
MINIMUM_THRESHOLD = 0.3
