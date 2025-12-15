from utils.hf_chat import hf_chat
import re
from cores.config import ROUTER_MODEL

DEBUG_SYSTEM = """
You are an AI debugging assistant.
If text is NOT a Python error → reply exactly: "Đây không phải lỗi, vui lòng nhập lỗi Python."
If it IS a real Python traceback → explain cause + fix.
Return plain text only.
"""

def is_python_error(text):
    patterns = [
        r"Traceback \(most recent call last\):",
        r"[A-Za-z]+Error:",
        r"Exception:",
        r"File \".+\", line \d+"
    ]
    return any(re.search(p, text) for p in patterns)

def debug_error(err):
    if not is_python_error(err):
        return "Đây không phải lỗi, vui lòng nhập lỗi Python."

    return hf_chat([
        {"role": "system", "content": DEBUG_SYSTEM},
        {"role": "user", "content": err}
    ], ROUTER_MODEL)
