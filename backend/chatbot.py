from backend.rag.mongo_rag import retrieve_context
from backend.utils.hf_chat import hf_chat

def ask_ai(user_query):
    context = retrieve_context(user_query)

    system_prompt = """
    Bạn là chuyên gia du lịch Việt Nam.
    Hãy trả lời dựa trên dữ liệu MongoDB đã cung cấp.
    Nếu không tìm thấy thông tin, hãy nói bạn không chắc chắn.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
    ]

    answer = hf_chat(messages)
    return answer, context
