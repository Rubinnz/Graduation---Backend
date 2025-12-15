import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity, pairwise_distances
from sentence_transformers import SentenceTransformer
from backend.db.mongo_client import db
from backend.utils.hf_chat import hf_chat

emotion = db["emotion"]
topics_col = db["topics"]
keywords_col = db["topic_keywords"]

def extract_keywords(texts, top_k=10):
    words = {}
    for t in texts:
        for w in t.lower().split():
            words[w] = words.get(w, 0) + 1
    sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in sorted_words[:top_k]]

def name_topic(keywords):
    prompt = [
        {"role": "system", "content": "Return a short topic name under 4 words."},
        {"role": "user", "content": ", ".join(keywords)}
    ]
    return hf_chat(prompt).strip()

def auto_topic_count(vecs):
    n = len(vecs)
    base = np.log(n)
    d = pairwise_distances(vecs[: min(300, n)], metric="cosine").mean()
    factor = 4.0 if d < 0.25 else 5.0 if d < 0.35 else 6.0
    est = int(base * factor)
    return max(6, min(20, est))

def topic_extract():
    docs = list(emotion.find({}, {"_id": 0}))
    if not docs:
        topics_col.delete_many({})
        keywords_col.delete_many({})
        return "topics"

    texts = [d["vietnam_segment"] for d in docs]

    embed = SentenceTransformer("BAAI/bge-base-en-v1.5")
    vecs = embed.encode(texts, show_progress_bar=False)

    n_clusters = auto_topic_count(vecs)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    clusters = kmeans.fit_predict(vecs)
    centroids = kmeans.cluster_centers_

    topic_map = {}
    for idx, c in enumerate(clusters):
        topic_map.setdefault(c, []).append(texts[idx])

    topic_keywords = {}
    for tid, tlist in topic_map.items():
        topic_keywords[tid] = extract_keywords(tlist)

    topic_names = {}
    for tid, kw in topic_keywords.items():
        topic_names[tid] = name_topic(kw)

    topic_probs = cosine_similarity(vecs, centroids).max(axis=1)

    out = []
    for d, tid, prob in zip(docs, clusters, topic_probs):
        d["topic"] = int(tid)
        d["topic_name"] = topic_names[tid]
        d["topic_prob"] = float(prob)
        out.append(d)

    topics_col.delete_many({})
    topics_col.insert_many(out)

    kw_out = []
    for tid, kw in topic_keywords.items():
        kw_out.append({
            "topic": int(tid),
            "keywords": kw,
            "topic_name": topic_names[tid]
        })

    keywords_col.delete_many({})
    keywords_col.insert_many(kw_out)

    return "topics"
