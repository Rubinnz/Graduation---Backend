from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import emoji

from backend.cores.pipeline_runner import execute_tool
from backend.rag.mongo_rag import retrieve_context
from backend.utils.hf_chat import hf_chat
from backend.db.mongo_client import db

app = FastAPI() 

class Query(BaseModel):
    query: str

class ToolRequest(BaseModel):
    tool: str
    args: dict = {}

class UploadRequest(BaseModel):
    collection: str
    records: list

def clean_text(text: str):
    text = emoji.replace_emoji(text, "")
    text = re.sub(r'[*_`~#>\[\]+\-]', "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

@app.get("/")
def home():
    return {"message": "Vietnam Travel API is running"}

@app.post("/chat")
def chat_api(data: Query):
    q = data.query
    ctx = retrieve_context(q)
    system_prompt = (
        "Bạn là chuyên gia du lịch Việt Nam với phong cách thân thiện và hơi nhí nhảnh. "
        "Bạn nói chuyện tự nhiên, gần gũi, giống như một người bạn am hiểu du lịch. "
        "Cách trả lời phải mềm mại, mượt mà, không gượng ép và không quá dài. "
        "Không dùng emoji. Không dùng Markdown hoặc bất kỳ ký tự định dạng như *, _, ~, -, +, #, >, `. "
        "Không tạo danh sách liệt kê hay bullet. "
        "Nếu câu hỏi không liên quan đến du lịch Việt Nam, hãy từ chối lịch sự. "
        "Nếu có Context phù hợp thì dùng. Nếu không nhưng vẫn thuộc du lịch Việt Nam, trả lời bằng kiến thức chung. "
        "Không trả lời ngoài phạm vi."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion:\n{q}"}
    ]
    answer = clean_text(hf_chat(messages))
    return {"answer": answer, "context": ctx}

@app.post("/run-tool")
def run_tool(req: ToolRequest):
    result = execute_tool(req.tool, req.args)
    csv_content = None
    if isinstance(result, str) and result.lower().endswith(".csv"):
        try:
            with open(result, "r", encoding="utf-8") as f:
                csv_content = f.read()
        except:
            pass
    return {"result": result, "csv": csv_content}

@app.post("/upload")
def upload_to_mongo(req: UploadRequest):
    col = db[req.collection]
    if not isinstance(req.records, list):
        raise HTTPException(status_code=400, detail="records must be a list")
    if len(req.records) == 0:
        return {"inserted": 0}
    res = col.insert_many(req.records)
    return {"inserted": len(res.inserted_ids)}

@app.get("/fetch/{collection}")
def fetch(collection: str):
    if collection not in db.list_collection_names():
        return {"data": []}
    docs = list(db[collection].find({}, {"_id": 0}))
    return {"data": docs}
