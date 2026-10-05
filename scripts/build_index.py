#build_index.py
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from config import (
    EMBEDDING_MODEL_NAME,
    INDEX_PATH,
    DATABASE_PATH,
)
from app.db import count_documents, load_all_documents


def main() -> None:
    print("Loading documents from:", DATABASE_PATH)
    documents = load_all_documents()
    if not documents:
        raise ValueError(f"No documents found in {DATABASE_PATH}")

    texts = [document["text"] for document in documents]
    vector_ids = np.array(
        [document["vector_id"] for document in documents],
        dtype=np.int64,
    )

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    base_index = faiss.IndexFlatIP(embeddings.shape[1])
    index = faiss.IndexIDMap2(base_index)
    index.add_with_ids(embeddings, vector_ids)

    if index.ntotal != count_documents():
        raise ValueError(
            f"Index and database are inconsistent: "
            f"{index.ntotal} != {count_documents()}"
        )

    faiss.write_index(index, str(INDEX_PATH))

    print(f"Loaded {len(documents)} documents")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Indexed vectors: {index.ntotal}")
    print(f"Saved index to {INDEX_PATH}")


if __name__ == "__main__":
    main()
