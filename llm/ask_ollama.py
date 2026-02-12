import ollama
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

def load_file(file_path):
    with open(BASE_DIR.parent / file_path, "r") as f:
        return f.read()


def load_profile():
    return load_file("prompts/profile.txt")


def load_rules():
    return load_file("prompts/evaluation_rules.txt")


def load_prompt_template():
    return load_file("prompts/job_evaluator.txt")
    

def build_prompt(job_description, candidate_profile, rules):
    template = load_prompt_template()
    return template.format(
        candidate_profile=candidate_profile,
        evaluation_rules=rules,
        job_description=job_description
    )


def analyze_with_ollama(job):
    profile = load_profile()
    rules = load_rules()
    prompt = build_prompt(job.description, profile, rules)
    messages = [
        {'role': 'system', 'content': 'You are a professional career advisor and job matching assistant for a backend software engineer.'},
        {'role': 'user', 'content': f'{prompt}'}
    ]
    
    response = ollama.chat(
        model='qwen3:8b',
        messages=messages
    )
    text = response['message']['content']
    return {"link": job.url, "ollama_answer": text}
    # lines = text.strip().splitlines()
    # decision, reason = None, ""
    # for line in lines:
    #     if line.lower().startswith("decision:"):
    #         decision = line.split(":",1)[1].strip().upper()
    #     elif line.lower().startswith("reason:"):
    #         reason = line.split(":",1)[1].strip()
    # return {"link": job.url, "decision": decision, "reason": reason}