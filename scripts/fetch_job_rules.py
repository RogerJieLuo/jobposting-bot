from model.job import Job


def is_under_100(applicants: int) -> bool:
    if not applicants:
        return True
    return applicants < 100


def is_target_software_role(title: str) -> bool:
    title_lc = title.lower()
    # 1. senior 以上直接排除
    senior_keywords = [
        # "sr."
        # "senior",
        "staff",
        "principal",
        "lead",
        "architect",
        "manager",
        "director",
        "vp",
        "head"
    ]
    for kw in senior_keywords:
        if kw in title_lc:
            return False

    # 2. 软件工程相关关键词
    software_keywords = [
        "software",
        "engineer",
        "developer",
        "sde",
        "backend",
        "platform",
        # "front end",
        # "frontend",
        # "mobile",
        # "ios",
        # "android",
        "full stack",
        "full-stack",
        "fullstack"
    ]

    for kw in software_keywords:
        if kw in title_lc:
            return True

    return False