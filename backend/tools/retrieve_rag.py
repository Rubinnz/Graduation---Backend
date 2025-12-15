from backend.rag.faiss_index import search

def retrieve_rag(args):
    query = args.get("query", "")
    results = search(query)
    return "\n\n".join(results)
