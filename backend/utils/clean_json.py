def clean_json(raw):
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "").strip()
    return raw
