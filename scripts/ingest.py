import importlib

from config import ACTIVE_SOURCE, DATABASE_PATH
from app.db import init_schema, save_documents_to_db


def main() -> None:
    connector = importlib.import_module(f"scripts.connectors.{ACTIVE_SOURCE}")
    documents = connector.fetch()

    init_schema()
    save_documents_to_db(documents)

    print(f"Downloaded {len(documents)} documents")
    print(f"Saved to {DATABASE_PATH}")


if __name__ == "__main__":
    main()
