from backend.db.mongo_client import tourism
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def build_faiss_index():
    docs = [doc["content"] for doc in tourism.find()]
    embeddings = embedder.encode(docs, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, docs

faiss_index, stored_docs = build_faiss_index()


def retrieve_context(query, top_k=8):
    q = query.lower()

    # ===== ROUTING CHO HÀNH CHÍNH =====
    admin_keywords = ["tỉnh", "province", "đơn vị hành chính", "administrative"]
    if any(k in q for k in admin_keywords):
        doc = tourism.find_one({"sub_category": "administration"})
        if doc:
            return doc["content"]

    # ===== ROUTING CHO ẨM THỰC =====
    food_keywords = ["ẩm thực", "food", "ăn uống", "đặc sản", "món ăn", "phở", "bánh mì"]
    if any(k in q for k in food_keywords):
        docs = tourism.find({"category": "cuisine"})
        return "\n".join([d["content"] for d in docs])

    # ===== ROUTING CHO VĂN HÓA =====
    culture_keywords = ["văn hóa", "culture", "truyền thống", "lễ hội"]
    if any(k in q for k in culture_keywords):
        docs = tourism.find({"category": "culture"})
        return "\n".join([d["content"] for d in docs])

    # ===== ROUTING CHO SÔNG NƯỚC / MIỀN TÂY =====
    river_keywords = ["sông nước", "river", "miền tây", "mekong", "floating"]
    if any(k in q for k in river_keywords):
        docs = tourism.find({"metadata.tags": "floating_market"})
        return "\n".join([d["content"] for d in docs])

    # ===== ROUTING CHO NÚI / ĐỒI / PHONG CẢNH =====
    mountain_keywords = ["núi", "mountain", "đồi", "cảnh đẹp", "karst", "terraced"]
    if any(k in q for k in mountain_keywords):
        docs = tourism.find({"metadata.type": {"$in": ["geopark", "natural_heritage"]}})
        return "\n".join([d["content"] for d in docs])

    # ===== ROUTING CHO DI SẢN UNESCO =====
    unesco_keywords = ["unesco", "di sản", "heritage"]
    if any(k in q for k in unesco_keywords):
        docs = tourism.find({"content": {"$regex": "UNESCO", "$options": "i"}})
        return "\n".join([d["content"] for d in docs])

    # ===== RAG FAISS FALLBACK =====
    query_emb = embedder.encode([query], convert_to_numpy=True)
    _, idx = faiss_index.search(query_emb, top_k)

    return "\n".join(stored_docs[i] for i in idx[0])
