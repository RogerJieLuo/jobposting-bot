import re


def extract_recommendation(text: str):
    if not text:
        return None
    m = re.search(r"clear recommendation\s*:\s*(apply|consider|skip)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).lower()

    m = re.search(r"\brecommendation\s*:\s*(apply|consider|skip)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).lower()

    m = re.search(r"\b(apply|consider|skip)\b", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).lower()
    return None
