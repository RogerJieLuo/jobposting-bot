import ollama
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Per-country prompt dir: prompts/<country>/ (e.g. prompts/canada/, prompts/japan/). Fallback: prompts/default/
def _prompt_dir(country=None):
    key = (country or "default").strip().lower()
    return PROJECT_ROOT / "prompts" / key


def _load_prompt_file(filename, country=None):
    d = _prompt_dir(country)
    path = d / filename
    if not path.exists():
        path = _prompt_dir("default") / filename
    with open(path, "r") as f:
        return f.read()


def load_profile(country=None):
    return _load_prompt_file("profile.txt", country)


def load_rules(country=None):
    return _load_prompt_file("evaluation_rules.txt", country)


def load_prompt_template(country=None):
    return _load_prompt_file("job_evaluator.txt", country)
    

def build_prompt(job_description, candidate_profile, rules, country=None):
    template = load_prompt_template(country)
    return template.format(
        candidate_profile=candidate_profile,
        evaluation_rules=rules,
        job_description=job_description
    )


def analyze_with_ollama(job):
    country = getattr(job, "country", None) or "default"
    profile = load_profile(country)
    rules = load_rules(country)
    prompt = build_prompt(job.description, profile, rules, country)
    messages = [
        {'role': 'system', 'content': 'You are a professional career advisor and job matching assistant for a backend software engineer.'},
        {'role': 'user', 'content': f'{prompt}'}
    ]
    
    response = ollama.chat(
        model='qwen3:8b',
        messages=messages
    )
    text = response['message']['content']
    decision = extract_recommendation(text)
    return {"link": job.url, "ollama_answer": text, "decision": decision}
    # lines = text.strip().splitlines()
    # decision, reason = None, ""
    # for line in lines:
    #     if line.lower().startswith("decision:"):
    #         decision = line.split(":",1)[1].strip().upper()
    #     elif line.lower().startswith("reason:"):
    #         reason = line.split(":",1)[1].strip()
    # return {"link": job.url, "decision": decision, "reason": reason}


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
