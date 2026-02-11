import re
from bs4 import BeautifulSoup
from logger_util import logger
from model.job import Job


JOBS_LIMIT = 50

def parse_job_search_list(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for li in soup.select("li"):
        job = _parse_job_card(li)
        if not job:
            continue
        jobs.append(_parse_job_card(li))
        if len(jobs) == JOBS_LIMIT:
            break
    return jobs

def _parse_job_card(li) -> Job:
    title_tag = li.select_one("h3")
    company_tag = li.select_one("h4")
    link_tag = li.select_one("a")
    location = li.find("span", class_="job-search-card__location")
    id = li.select_one("data-job-id")

    if not title_tag or not link_tag:
        return

    return Job(
        id=id.get_text(strip=True) if id else "",
        title=title_tag.get_text(strip=True),
        url=link_tag["href"],
        company=company_tag.get_text(strip=True) if company_tag else "",
        location=location.get_text(strip=True) if location else ""
    )


def parse_job_applicant_and_description(html):
    soup = BeautifulSoup(html, "html.parser")

    number_of_applicants = _parse_numeber_of_applicant(soup)
    job_description = _parse_job_description(soup)

    return (number_of_applicants, job_description)

def _parse_numeber_of_applicant(soup):
    applicant_div = soup.select_one(".topcard__flavor-row .num-applicants__caption")
    if applicant_div:
        matches = re.findall(r'\d+', applicant_div.get_text(strip=True))
        return int(matches[-1]) if matches else None
    else:
        logger.warning(">> No applicant div")
    return None


def _parse_job_description(soup):
    desc_div = soup.find("div", class_="description__text")  # 根据实际 class 调整
    if desc_div:
        return desc_div.get_text(separator="\n", strip=True)
    else:
        logger.warning(">> no job desc")
    return None