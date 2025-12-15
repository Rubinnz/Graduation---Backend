import requests
from backend.cores.config import HF_API_KEY, ROUTER_MODEL

def hf_chat(messages):
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    payload = {
        "model": ROUTER_MODEL,
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.2
    }

    r = requests.post(url, json=payload, headers=headers)
    data = r.json()
    
    if "generated_text" in data:
        return data["generated_text"]

    if "choices" in data:
        choice = data["choices"][0]

        if "text" in choice:
            return choice["text"]

        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"]

    return "Không thể tạo câu trả lời từ model."
