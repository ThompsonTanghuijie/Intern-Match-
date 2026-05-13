import re
from dataclasses import dataclass
from html import unescape

from bs4 import BeautifulSoup

from app.schemas import RawJob


SKILL_ALIASES: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "Java": [r"\bjava\b"],
    "C++": [r"\bc\+\+\b", r"\bcpp\b"],
    "SQL": [r"\bsql\b"],
    "PostgreSQL": [r"\bpostgres(?:ql)?\b"],
    "MongoDB": [r"\bmongodb\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "React": [r"\breact\b", r"\breact\.js\b"],
    "FastAPI": [r"\bfastapi\b"],
    "Spark": [r"\bspark\b", r"\bapache spark\b"],
    "Airflow": [r"\bairflow\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Data Engineering": [r"\bdata engineering\b", r"\bdata engineer(?:ing)?\b"],
    "TypeScript": [r"\btypescript\b"],
    "Go": [r"\bgolang\b", r"\bgo\b"],
    "Linux": [r"\blinux\b"],
    "Playwright": [r"\bplaywright\b"],
    "Selenium": [r"\bselenium\b"],
}


@dataclass(frozen=True)
class MarkdownTable:
    headers: list[str]
    rows: list[list[str]]


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    if "<" in value and ">" in value:
        soup = BeautifulSoup(value, "html.parser")
        text = soup.get_text(" ", strip=True)
    else:
        text = value
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_link(cell: str) -> str | None:
    markdown_match = re.search(r"\[[^\]]+\]\(([^)]+)\)", cell)
    if markdown_match:
        return markdown_match.group(1).strip()
    soup = BeautifulSoup(cell, "html.parser")
    link = soup.find("a")
    if link and link.get("href"):
        return str(link["href"]).strip()
    url_match = re.search(r"https?://[^\s)>]+", cell)
    return url_match.group(0) if url_match else None


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    cells: list[str] = []
    current = []
    in_code = False
    escape = False
    for char in stripped:
        if char == "\\" and not escape:
            escape = True
            current.append(char)
            continue
        if char == "`" and not escape:
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        escape = False
    cells.append("".join(current).strip())
    return cells


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", cell.strip()) for cell in cells if cell.strip())


def parse_markdown_tables(markdown: str) -> list[MarkdownTable]:
    lines = markdown.splitlines()
    tables: list[MarkdownTable] = []
    index = 0
    while index < len(lines) - 1:
        line = lines[index]
        next_line = lines[index + 1]
        if "|" not in line or "|" not in next_line:
            index += 1
            continue
        headers = split_markdown_row(line)
        maybe_sep = split_markdown_row(next_line)
        if not headers or not is_separator_row(maybe_sep):
            index += 1
            continue
        rows: list[list[str]] = []
        index += 2
        while index < len(lines) and "|" in lines[index].strip():
            row = split_markdown_row(lines[index])
            if len(row) >= 2:
                rows.append(row)
            index += 1
        tables.append(MarkdownTable(headers=headers, rows=rows))
    return tables


def find_column(headers: list[str], candidates: list[str]) -> int | None:
    normalized = [normalize_text(h).lower() for h in headers]
    for candidate in candidates:
        for idx, header in enumerate(normalized):
            if candidate in header:
                return idx
    return None


def infer_job_type(text: str) -> str:
    lowered = text.lower()
    if "new grad" in lowered or "graduate" in lowered:
        return "new_grad"
    if "intern" in lowered or "internship" in lowered:
        return "internship"
    if "co-op" in lowered or "coop" in lowered:
        return "coop"
    return "unknown"


def infer_season(text: str) -> str | None:
    match = re.search(r"\b(2026|summer 2026|fall 2026|spring 2026|winter 2026)\b", text, flags=re.I)
    return match.group(0) if match else "2026"


def extract_skills(text: str) -> list[str]:
    matches: list[str] = []
    for skill, patterns in SKILL_ALIASES.items():
        if any(re.search(pattern, text, flags=re.I) for pattern in patterns):
            matches.append(skill)
    return sorted(matches)


def parse_github_markdown_jobs(markdown: str, source_url: str) -> list[RawJob]:
    jobs: list[RawJob] = []
    for table in parse_markdown_tables(markdown):
        company_idx = find_column(table.headers, ["company", "employer"])
        title_idx = find_column(table.headers, ["role", "position", "title", "job"])
        location_idx = find_column(table.headers, ["location"])
        apply_idx = find_column(table.headers, ["application", "apply", "link"])
        if company_idx is None or title_idx is None:
            continue
        for row in table.rows:
            max_idx = max(i for i in [company_idx, title_idx, location_idx, apply_idx] if i is not None)
            if len(row) <= max_idx:
                continue
            company = normalize_text(row[company_idx])
            title = normalize_text(row[title_idx])
            if not company or not title or company.lower() in {"company", "name"}:
                continue
            location = normalize_text(row[location_idx]) if location_idx is not None else None
            apply_cell = row[apply_idx] if apply_idx is not None and len(row) > apply_idx else ""
            apply_url = extract_link(apply_cell) or extract_link(row[title_idx])
            raw_text = " ".join(normalize_text(cell) for cell in row)
            jobs.append(
                RawJob(
                    company=company,
                    title=title,
                    location=location or None,
                    job_type=infer_job_type(raw_text),
                    season=infer_season(raw_text),
                    apply_url=apply_url,
                    source_url=source_url,
                    raw_text=raw_text,
                )
            )
    jobs.extend(parse_html_table_jobs(markdown, source_url))
    return jobs


def parse_html_table_jobs(markdown: str, source_url: str) -> list[RawJob]:
    if "<table" not in markdown.lower():
        return []
    soup = BeautifulSoup(markdown, "html.parser")
    jobs: list[RawJob] = []
    for table in soup.find_all("table"):
        headers = [normalize_text(str(cell)) for cell in table.find_all("th")]
        company_idx = find_column(headers, ["company", "employer"])
        title_idx = find_column(headers, ["role", "position", "title", "job"])
        location_idx = find_column(headers, ["location"])
        apply_idx = find_column(headers, ["application", "apply", "link"])
        if company_idx is None or title_idx is None:
            continue
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if not cells:
                continue
            max_idx = max(i for i in [company_idx, title_idx, location_idx, apply_idx] if i is not None)
            if len(cells) <= max_idx:
                continue
            cell_html = [str(cell) for cell in cells]
            company = normalize_text(cell_html[company_idx])
            title = normalize_text(cell_html[title_idx])
            if not company or not title:
                continue
            location = normalize_text(cell_html[location_idx]) if location_idx is not None else None
            apply_cell = cell_html[apply_idx] if apply_idx is not None else ""
            apply_url = extract_link(apply_cell) or extract_link(cell_html[title_idx])
            raw_text = " ".join(normalize_text(cell) for cell in cell_html)
            jobs.append(
                RawJob(
                    company=company,
                    title=title,
                    location=location or None,
                    job_type=infer_job_type(raw_text),
                    season=infer_season(raw_text),
                    apply_url=apply_url,
                    source_url=source_url,
                    raw_text=raw_text,
                )
            )
    return jobs
