import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

index = faiss.IndexFlatL2(384)
stored_chunks = []

def add_code_file(path):
    global stored_chunks

    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # chunk file code
    chunks = []
    lines = code.split("\n")
    batch = []

    for line in lines:
        batch.append(line)
        if len(batch) >= 40:          # chunk 40 dòng/lần
            chunks.append("\n".join(batch))
            batch = []

    if batch:
        chunks.append("\n".join(batch))

    stored_chunks.extend(chunks)

    vectors = embedding_model.encode(chunks)
    index.add(vectors)

def build_code_index(folder="tools"):
    for f in os.listdir(folder):
        if f.endswith(".py"):
            add_code_file(os.path.join(folder, f))

def search_code(query, top_k=5):
    query_vec = embedding_model.encode([query])
    D, I = index.search(np.array(query_vec), top_k)
    return [stored_chunks[i] for i in I[0]]
