from backend.db.mongo_client import db
import re
import emoji

raw = db["raw_tweets"]
merged = db["merged"]

def normalize_text(t):
    if not t:
        return ""
    t = t.lower()
    t = emoji.replace_emoji(t, "")
    t = re.sub(r"http\S+|www\.\S+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def merge_data():
    docs = list(raw.find({}, {"_id": 0}))

    seen_urls = set()
    seen_text = set()
    seen_norm = set()

    out = []

    for d in docs:
        url = d.get("url")
        text = d.get("tweet", "")
        norm = normalize_text(text)

        if url and url in seen_urls:
            continue
        if text and text in seen_text:
            continue
        if norm and norm in seen_norm:
            continue

        if url:
            seen_urls.add(url)
        if text:
            seen_text.add(text)
        if norm:
            seen_norm.add(norm)

        out.append(d)

    merged.delete_many({})
    if out:
        merged.insert_many(out)

    return "merged"
