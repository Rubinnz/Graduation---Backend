import os
from backend.rag.faiss_code_index import search_code

def retrieve_rag_code(args):
    """
    args = { "query": "...", "top_k": 5 }
    """
    query = args.get("query", "")
    top_k = args.get("top_k", 5)

    results = search_code(query, top_k=top_k)

    return "\n\n".join(results)
