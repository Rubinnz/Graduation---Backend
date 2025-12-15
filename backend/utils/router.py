import json
from utils.hf_chat import hf_chat
from utils.clean_json import clean_json
from utils.normalize_plan import normalize_plan
from cores.config import ROUTER_MODEL

SYSTEM_PROMPT = """
You are a strict JSON router for an AI automation pipeline.

You MUST ALWAYS output valid JSON in one of TWO formats only:

1) CHAT RESPONSE:
{"mode": "CHAT", "response": "<message>"}

2) TOOL CALL:
{"mode": "TOOL", "tool": "<tool_name>", "args": {...}}

Rules:
- NEVER output explanations, errors, descriptions, roles, system info, or natural language outside JSON.
- NEVER output keys other than: mode, response, tool, args.
- If the user message is unclear, reply:
{"mode": "CHAT", "response": "Tôi không hiểu yêu cầu của bạn."}

Allowed tools:
crawl_data,
merge_data,
filter_vietnam,
sentiment_classify,
emotion_classify,
topic_extract,
topic_keywords,
retrieve_rag,
retrieve_rag_code
"""

def router(user_message):

    raw = hf_chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ], ROUTER_MODEL)

    raw = clean_json(raw)

    try:
        return normalize_plan(json.loads(raw))
    except:
        pass

    s = raw.find("{")
    e = raw.rfind("}")

    if s != -1 and e != -1:
        try:
            return normalize_plan(json.loads(raw[s:e+1]))
        except:
            pass

    return {"mode": "CHAT", "response": raw}
