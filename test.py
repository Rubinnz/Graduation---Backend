import os
import fitz  # pymupdf
import requests
import tiktoken
from pymongo import MongoClient
from dotenv import load_dotenv

# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_EMBED_MODEL = os.getenv("HF_EMBED_MODEL")

if not all([MONGO_URI, HF_API_KEY, HF_EMBED_MODEL]):
    raise RuntimeError("Thiếu biến môi trường trong .env")

# =====================================================
# MONGODB
# =====================================================
client = MongoClient(MONGO_URI)
db = client["vietnam_ai"]
tourism = db["tourism"]

# =====================================================
# HUGGINGFACE EMBEDDING API
# =====================================================
HF_EMBED_URL = (
    f"https://api-inference.huggingface.co/pipeline/feature-extraction/"
    f"{HF_EMBED_MODEL}"
)

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

def get_embedding(text: str):
    payload = {
        "inputs": text,
        "options": {"wait_for_model": True}
    }

    r = requests.post(
        HF_EMBED_URL,
        headers=HF_HEADERS,
        json=payload,
        timeout=60
    )
    r.raise_for_status()
    data = r.json()

    # HF trả về [tokens][dim] hoặc [dim]
    if isinstance(data, list) and isinstance(data[0], list):
        # mean pooling
        return [sum(col) / len(col) for col in zip(*data)]

    return data

# =====================================================
# TOKENIZER (CHUNK AN TOÀN)
# =====================================================
tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_text(text, chunk_size=400, overlap=80):
    tokens = tokenizer.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk = tokenizer.decode(chunk_tokens)

        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

# =====================================================
# READ PDF
# =====================================================
def read_pdf(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append({
                "page": i + 1,
                "text": text
            })

    return pages

# =====================================================
# INGEST PDF (CHỈ ADD FILE)
# =====================================================
def ingest_pdf(
    pdf_path: str,
    source_name: str,
    region: str | None = None
):
    pages = read_pdf(pdf_path)
    inserted = 0

    for page in pages:
        chunks = chunk_text(page["text"])

        for idx, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)

            doc = {
                "text": chunk,
                "embedding": embedding,
                "page": page["page"],
                "chunk_id": f"p{page['page']}_c{idx}",
                "source": source_name,
                "region": region
            }

            tourism.insert_one(doc)
            inserted += 1

    print(f"✅ Đã add {inserted} chunks từ file: {source_name}")

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    ingest_pdf(
        pdf_path="D:/KLTN-Backend/data/VN.pdf",
        source_name="Chào Việt Nam – Cẩm nang Du lịch",
        region="Việt Nam"
    )
