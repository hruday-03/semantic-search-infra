"""SQLite storage for document metadata (PMID as primary key)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from config import DATABASE_PATH
from scripts.connectors.base import Document

DOCUMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    vector_id INTEGER NOT NULL UNIQUE,
    source TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}'
);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def document_to_row(document: Document) -> dict[str, Any]:
    metadata = dict(document.get("metadata") or {})
    document_id = document["id"]

    if document_id.isdigit():
        vector_id = int(document_id)
    else:
        vector_id = abs(hash(document_id)) % (2**63 - 1)

    title = metadata.pop("title", "")
    source = metadata.pop("source", "unknown")

    return {
        "id": document_id,
        "vector_id": vector_id,
        "source": source,
        "title": title,
        "text": document["text"],
        "metadata": json.dumps(metadata, ensure_ascii=False),
    }


def save_documents_to_db(documents: list[Document]) -> None:
    rows = [document_to_row(document) for document in documents]
    upsert_documents(rows)


def init_schema(connection: sqlite3.Connection | None = None) -> None:
    owns_connection = connection is None
    if owns_connection:
        connection = connect()

    try:
        connection.execute(DOCUMENTS_SCHEMA)
        connection.commit()
    finally:
        if owns_connection:
            connection.close()


def upsert_document(
    document: dict[str, Any],
    connection: sqlite3.Connection | None = None,
) -> None:
    owns_connection = connection is None
    if owns_connection:
        connection = connect()
        init_schema(connection)

    try:
        connection.execute(
            """
            INSERT INTO documents (id, vector_id, source, title, text, metadata)
            VALUES (:id, :vector_id, :source, :title, :text, :metadata)
            ON CONFLICT(id) DO UPDATE SET
                vector_id = excluded.vector_id,
                source = excluded.source,
                title = excluded.title,
                text = excluded.text,
                metadata = excluded.metadata
            """,
            {
                "id": document["id"],
                "vector_id": document["vector_id"],
                "source": document["source"],
                "title": document["title"],
                "text": document["text"],
                "metadata": document["metadata"],
            },
        )
        if owns_connection:
            connection.commit()
    finally:
        if owns_connection:
            connection.close()


def upsert_documents(
    documents: list[dict[str, Any]],
    connection: sqlite3.Connection | None = None,
) -> None:
    owns_connection = connection is None
    if owns_connection:
        connection = connect()
        init_schema(connection)

    try:
        for document in documents:
            upsert_document(document, connection)
        connection.commit()
    finally:
        if owns_connection:
            connection.close()


def _row_to_document(row: sqlite3.Row) -> dict[str, Any]:
    document = dict(row)
    document["metadata"] = json.loads(document["metadata"])
    return document


def get_by_id(
    document_id: str,
    connection: sqlite3.Connection | None = None,
) -> dict[str, Any] | None:
    owns_connection = connection is None
    if owns_connection:
        connection = connect()

    try:
        row = connection.execute(
            "SELECT id, vector_id, source, title, text, metadata FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        return _row_to_document(row) if row else None
    finally:
        if owns_connection:
            connection.close()


def get_by_vector_ids(
    vector_ids: list[int],
    connection: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    if not vector_ids:
        return []

    owns_connection = connection is None
    if owns_connection:
        connection = connect()

    try:
        placeholders = ",".join("?" for _ in vector_ids)
        rows = connection.execute(
            f"""
            SELECT id, vector_id, source, title, text, metadata
            FROM documents
            WHERE vector_id IN ({placeholders})
            """,
            vector_ids,
        ).fetchall()
        return [_row_to_document(row) for row in rows]
    finally:
        if owns_connection:
            connection.close()


def load_all_documents(
    connection: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    owns_connection = connection is None
    if owns_connection:
        connection = connect()

    try:
        rows = connection.execute(
            """
            SELECT id, vector_id, source, title, text, metadata
            FROM documents
            ORDER BY vector_id
            """
        ).fetchall()
        return [_row_to_document(row) for row in rows]
    finally:
        if owns_connection:
            connection.close()


def count_documents(connection: sqlite3.Connection | None = None) -> int:
    owns_connection = connection is None
    if owns_connection:
        connection = connect()

    try:
        row = connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
        return int(row["count"])
    finally:
        if owns_connection:
            connection.close()


def clear_documents(connection: sqlite3.Connection | None = None) -> None:
    owns_connection = connection is None
    if owns_connection:
        connection = connect()
        init_schema(connection)

    try:
        connection.execute("DELETE FROM documents")
        connection.commit()
    finally:
        if owns_connection:
            connection.close()





