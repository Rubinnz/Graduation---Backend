import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

index = faiss.IndexFlatL2(384)
stored_chunks = []

def add_documents(texts):
    global stored_chunks
    stored_chunks.extend(texts)
    vectors = embedding_model.encode(texts)         
    index.add(vectors)

def search(query, top_k=5):
    if len(stored_chunks) == 0 or index.ntotal == 0:
        return ["FAISS index is empty. Please add documents first."]

    if index.ntotal != len(stored_chunks):
        return ["FAISS index mismatch. Please rebuild FAISS index."]

    q_vec = embedding_model.encode([query])
    D, I = index.search(np.array(q_vec), top_k)

    results = []
    for idx in I[0]:
        if isinstance(idx, int) and 0 <= idx < len(stored_chunks):
            results.append(stored_chunks[idx])

    if len(results) == 0:
        return ["No valid FAISS results found."]

    return results
