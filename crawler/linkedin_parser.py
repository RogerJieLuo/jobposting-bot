import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils.logger import logger
from model.job import Job


# Jobs per page (LinkedIn search returns ~25 per page). Must match fetch_job pagination.
PAGE_SIZE = 25


def parse_job_search_list(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for li in soup.select("li"):
        job = _parse_job_card(li)
        if not job:
            continue
        jobs.append(job)
        if len(jobs) == PAGE_SIZE:
            break
    return jobs


def _parse_job_card(li) -> Job:
    title_tag = li.select_one("h3")
    company_tag = li.select_one("h4")
    link_tag = li.select_one("a")
    location = li.find("span", class_="job-search-card__location")

    if not title_tag or not link_tag:
        return

    job_url = link_tag.get("href", "") or ""
    job_id = li.get("data-job-id") or link_tag.get("data-job-id") or _canonical_job_url(job_url) or ""

    return Job(
        id=job_id,
        title=title_tag.get_text(strip=True),
        url=job_url,
        company=company_tag.get_text(strip=True) if company_tag else "",
        location=location.get_text(strip=True) if location else "",
    )


def _canonical_job_url(url: str) -> str:
    """Drop query/fragment so tracking params don't break dedupe."""
    if not url:
        return ""
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        return url
    return f"{p.scheme}://{p.netloc}{p.path}"


def parse_job_applicant_and_description(html):
    soup = BeautifulSoup(html, "html.parser")

    number_of_applicants = _parse_numeber_of_applicant(soup)
    job_description = _parse_job_description(soup)

    return (number_of_applicants, job_description)


def _parse_numeber_of_applicant(soup):
    applicant_div = soup.select_one(".topcard__flavor-row .num-applicants__caption")
    if applicant_div:
        matches = re.findall(r"\d+", applicant_div.get_text(strip=True))
        return int(matches[-1]) if matches else None
    else:
        logger.warning(">> No applicant div")
    return None


def _parse_job_description(soup):
    desc_div = soup.find("div", class_="description__text")  # Adjust class if LinkedIn markup changes
    if desc_div:
        return desc_div.get_text(separator="\n", strip=True)
    else:
        logger.warning(">> no job desc")
    return None
