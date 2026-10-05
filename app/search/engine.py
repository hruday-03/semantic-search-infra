import faiss
from sentence_transformers import SentenceTransformer

from config import (
    EMBEDDING_MODEL_NAME,
    INDEX_PATH,
    MINIMUM_THRESHOLD,
)
from app.db import count_documents, get_by_vector_ids

if not INDEX_PATH.exists():
    raise FileNotFoundError(
        f"FAISS index file was not found: {INDEX_PATH}"
    )

index = faiss.read_index(str(INDEX_PATH))
model = SentenceTransformer(EMBEDDING_MODEL_NAME)
document_count = count_documents()

if index.ntotal != document_count:
    raise ValueError(
        f"Index and database are inconsistent: "
        f"{index.ntotal} != {document_count}"
    )


def search(query: str, top_k: int) -> list[dict]:
    query = query.strip()
    if not query:
        raise ValueError("Search query cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    actual_top_k = min(top_k, index.ntotal)
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    scores, vector_ids = index.search(query_embedding, actual_top_k)

    hit_ids = [
        int(vector_id)
        for score, vector_id in zip(scores[0], vector_ids[0])
        if vector_id != -1 and score >= MINIMUM_THRESHOLD
    ]
    documents_by_vector_id = {
        document["vector_id"]: document
        for document in get_by_vector_ids(hit_ids)
    }

    results = []
    for score, vector_id in zip(scores[0], vector_ids[0]):
        if vector_id == -1 or score < MINIMUM_THRESHOLD:
            continue

        document = documents_by_vector_id.get(int(vector_id))
        if document is None:
            continue

        results.append(
            {
                "score": float(score),
                "id": document["id"],
                "text": document["text"],
                "metadata": {
                    "source": document["source"],
                    "title": document["title"],
                    **document["metadata"],
                },
            }
        )

    return results
