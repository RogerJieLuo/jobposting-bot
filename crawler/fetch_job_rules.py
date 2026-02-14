def is_under_100(applicants: int) -> bool:
    if not applicants:
        return True
    return applicants < 100


def is_target_software_role(title: str) -> bool:
    title_lc = title.lower()
    # 1. Exclude senior+ roles (staff, principal, lead, etc.)
    senior_keywords = [
        "staff",
        "principal",
        "lead",
        "architect",
        "manager",
        "director",
        "vp",
        "head",
    ]
    for kw in senior_keywords:
        if kw in title_lc:
            return False

    # 2. Software-engineering-related keywords
    software_keywords = [
        "software",
        "engineer",
        "developer",
        "sde",
        "backend",
        "platform",
        "full stack",
        "full-stack",
        "fullstack",
    ]

    for kw in software_keywords:
        if kw in title_lc:
            return True

    return False
