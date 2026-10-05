#search_index.py
import faiss
from sentence_transformers import SentenceTransformer

from config import (
    EMBEDDING_MODEL_NAME,
    INDEX_PATH,
    MINIMUM_THRESHOLD,
)
from app.db import count_documents, get_by_vector_ids


def main() -> None:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"FAISS index file was not found: {INDEX_PATH}"
        )

    index = faiss.read_index(str(INDEX_PATH))
    document_count = count_documents()
    results_found = False

    if index.ntotal != document_count:
        raise ValueError(
            f"Index and database are inconsistent: "
            f"{index.ntotal} != {document_count}"
        )

    print(f"Loaded {document_count} documents")

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query = input("Enter your search query: ").strip()

    if not query:
        raise ValueError("Search query cannot be empty")

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    top_k = min(5, index.ntotal)

    scores, vector_ids = index.search(query_embedding, top_k)
    hit_ids = [
        int(vector_id)
        for score, vector_id in zip(scores[0], vector_ids[0])
        if vector_id != -1 and score >= MINIMUM_THRESHOLD
    ]
    documents_by_vector_id = {
        document["vector_id"]: document
        for document in get_by_vector_ids(hit_ids)
    }

    for rank, (score, vector_id) in enumerate(
        zip(scores[0], vector_ids[0]),
        start=1,
    ):
        if vector_id == -1 or score < MINIMUM_THRESHOLD:
            continue

        document = documents_by_vector_id.get(int(vector_id))
        if document is None:
            continue

        abstract = document["metadata"].get("abstract", "")
        results_found = True
        print("\n" + "=" * 70)
        print(f"Result {rank}")
        print(f"Score: {score:.4f}")
        print(f"PMID: {document['id']}")
        print(f"Title: {document['title']}")
        print(f"Abstract: {abstract[:500]}...")

    if not results_found:
        print("\nNo sufficiently relevant documents found.")


if __name__ == "__main__":
    main()
