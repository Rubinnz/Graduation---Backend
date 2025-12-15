import os
import warnings
warnings.filterwarnings("ignore")
import transformers
transformers.logging.set_verbosity_error()

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from tqdm import tqdm
from backend.db.mongo_client import db

filtered = db["filtered"]
sentiment = db["sentiment"]

MODEL_PATH = os.getenv("SENTIMENT_MODEL_PATH")
DEVICE = os.getenv("SENTIMENT_DEVICE")

LABEL_MAP = ["negative", "neutral", "positive"]

tokenizer_s = AutoTokenizer.from_pretrained(MODEL_PATH)
model_s = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH, dtype=torch.float16, use_safetensors=True
).to(DEVICE)
model_s.eval()

def classify_sentiment_batch(text_list, batch_size=64):
    out_labels, out_scores = [], []
    for i in tqdm(range(0, len(text_list), batch_size)):
        batch = text_list[i:i+batch_size]
        enc = tokenizer_s(batch, return_tensors="pt", padding=True, truncation=True, max_length=256)
        enc = {k: v.to(DEVICE) for k, v in enc.items()}
        with torch.no_grad():
            logits = model_s(**enc).logits
        probs = torch.softmax(logits, -1).cpu().numpy()
        lbl = probs.argmax(axis=1)
        score = probs.max(axis=1)
        out_labels.extend([LABEL_MAP[j] for j in lbl])
        out_scores.extend(score.tolist())
    return out_labels, out_scores

def sentiment_classify():
    docs = list(filtered.find({}, {"_id": 0}))
    if not docs:
        sentiment.delete_many({})
        return "sentiment"

    texts = [d["vietnam_segment"] for d in docs]
    labels, scores = classify_sentiment_batch(texts)

    out = []
    for d, lb, sc in zip(docs, labels, scores):
        d["sentiment"] = lb
        d["sentiment_score"] = float(sc)
        out.append(d)

    sentiment.delete_many({})
    sentiment.insert_many(out)

    return "sentiment"
