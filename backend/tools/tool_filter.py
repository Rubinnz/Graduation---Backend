import re
import emoji
from langdetect import detect
import nltk
from transformers import pipeline
from backend.db.mongo_client import db

for pkg in ["punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{pkg}")
    except LookupError:
        nltk.download(pkg)

merged = db["merged"]
filtered = db["filtered"]

tourism_clf = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/bge-m3-zeroshot-v2.0"
)

TOURISM_LABELS = [
    "The content expresses opinions, reviews, or experiences about Vietnam's tourism, destinations, attractions, travel services, or foreign tourists' impressions of Vietnam",
    "The content is not related to Vietnam tourism and does not evaluate travel experiences"
]

URL_RE = re.compile(r"http\S+|www\.\S+")
MENTION_RE = re.compile(r"[@#]\w+")
NON_ASCII = re.compile(r"[^A-Za-z0-9\s.,!?]")
MULTI_SPACE = re.compile(r"\s+")

VIET_KEYS = [
    "vietnam","viet nam","vn","hanoi","ha noi","saigon","sai gon","ho chi minh","hcmc",
    "hoi an","da nang","danang","halong","ha long","phu quoc","phuquoc","sapa","ha giang",
    "hagiang","nha trang","nhatrang","hue","mekong","tam coc","tamcoc","can tho","cantho",
    "dalat","da lat"
]

def clean_text(t):
    t = URL_RE.sub("", str(t))
    t = MENTION_RE.sub("", t)
    t = emoji.replace_emoji(t, "")
    t = NON_ASCII.sub(" ", t)
    return MULTI_SPACE.sub(" ", t).strip()

def is_english(t):
    t = t.strip()
    if not t:
        return False
    try:
        return detect(t[:200]) == "en"
    except:
        return False

def extract_segment(t):
    t = str(t)
    low = t.lower()
    if not any(k in low for k in VIET_KEYS):
        return ""
    sents = nltk.sent_tokenize(t)
    keep = [s for s in sents if any(k in s.lower() for k in VIET_KEYS)]
    return " ".join(keep)

def is_tourism_related(text):
    r = tourism_clf(text, TOURISM_LABELS)
    scores = dict(zip(r["labels"], r["scores"]))
    return scores[TOURISM_LABELS[0]] > scores[TOURISM_LABELS[1]]

def filter_vietnam():
    docs = list(merged.find({}, {"_id": 0}))
    out = []
    for d in docs:
        txt = clean_text(d.get("tweet", ""))
        if not txt:
            continue
        if not is_english(txt):
            continue
        seg = extract_segment(txt)
        if not seg.strip():
            continue
        if not is_tourism_related(txt):
            continue
        d["clean_tweet"] = txt
        d["vietnam_segment"] = seg
        out.append(d)

    filtered.delete_many({})
    if out:
        filtered.insert_many(out)

    return "filtered"
