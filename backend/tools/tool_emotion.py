import os
import warnings
warnings.filterwarnings("ignore")
import transformers
transformers.logging.set_verbosity_error()

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm
from backend.db.mongo_client import db

sentiment = db["sentiment"]
emotion = db["emotion"]

EMO_PATH = os.getenv("EMOTION_MODEL_PATH")
DEVICE = os.getenv("EMOTION_DEVICE")

tokenizer_e = AutoTokenizer.from_pretrained(EMO_PATH)

model_e = AutoModelForSequenceClassification.from_pretrained(
    EMO_PATH,
    use_safetensors=True
)

if DEVICE == "cuda":
    model_e = model_e.half()
else:
    model_e = model_e.float()

model_e = model_e.to(DEVICE)
model_e.eval()

emotion_labels = [
    "anger","anticipation","disgust","fear","joy",
    "love","optimism","pessimism","sadness","surprise","trust"
]


def classify_emotion_batch(text_list, batch_size=64):
    out_emo, out_score = [], []
    for i in tqdm(range(0, len(text_list), batch_size)):
        batch = text_list[i:i+batch_size]
        
        enc = tokenizer_e(batch, return_tensors="pt", padding=True, truncation=True, max_length=256)
        enc = {k: v.to(DEVICE) for k, v in enc.items()}

        with torch.no_grad():
            logits = model_e(**enc).logits

        probs = torch.sigmoid(logits).cpu().numpy()

        for p in probs:
            idx = p.argmax()
            out_emo.append(emotion_labels[idx])
            out_score.append(float(p[idx]))

    return out_emo, out_score



def emotion_classify():
    docs = list(sentiment.find({}, {"_id": 0}))
    if not docs:
        emotion.delete_many({})
        return "emotion"

    texts = [d.get("vietnam_segment", "").strip() for d in docs]
    texts = [t for t in texts if t]

    if not texts:
        emotion.delete_many({})
        return "emotion"

    emos, scores = classify_emotion_batch(texts)

    out = []
    for d, e, sc in zip(docs, emos, scores):
        d["emotion"] = e
        d["emotion_score"] = float(sc)
        out.append(d)

    emotion.delete_many({})
    emotion.insert_many(out)

    return "emotion"
