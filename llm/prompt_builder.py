from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


def load_company_screening_rules(country=None):
    return _load_prompt_file("company_screening_rules.txt", country)


def load_gemini_batch_prompt_template(country=None, include_company_screening=True):
    name = (
        "gemini_batch_job_evaluator.txt"
        if include_company_screening
        else "gemini_batch_job_evaluator_basic.txt"
    )
    return _load_prompt_file(name, country)


def build_prompt(
    job_description,
    candidate_profile,
    rules,
    company_name="",
    company_screening_rules="",
    company_context="",
    country=None,
    include_company_screening=False,
):
    template_name = "job_evaluator.txt" if include_company_screening else "job_evaluator_basic.txt"
    template = _load_prompt_file(template_name, country)
    return template.format(
        candidate_profile=candidate_profile,
        evaluation_rules=rules,
        company_name=company_name or "Unknown",
        company_screening_rules=company_screening_rules,
        company_context=company_context,
        job_description=job_description,
    )
