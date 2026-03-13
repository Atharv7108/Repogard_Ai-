import os
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from github import Github
from github.GithubException import GithubException, RateLimitExceededException


class AnalysisError(Exception):
    """Raised when repository analysis cannot be completed."""


GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-fast-reasoning")

AI_TASKS: Dict[str, str] = {
    "repository_health_score": (
        "Compute overall repository health score (0-100) using weighted rubric: "
        "maintainability 25%, security 25%, contributor resilience 20%, activity 15%, documentation 15%. "
        "Use only given repository context. No invented facts. "
        "Return JSON with keys: score (int), confidence (0-1 float), rationale (string), "
        "positives (array of strings), risks (array of strings), assumptions (array of strings), "
        "evidence_used (array of strings). Lower confidence if critical data is missing."
    ),
    "bus_factor": (
        "Estimate bus factor resilience score (0-100, higher is better) using contributor concentration. "
        "Scoring guide: top contributor share >60% => 10-35, 40-60% => 30-55, 25-40% => 50-75, <25% => 70-95. "
        "Use top contributors and recent activity signals only. "
        "Return JSON keys: bus_factor_percent (int), concentration_risk (low|medium|high), "
        "key_person_dependency (array of contributor logins), rationale (string), assumptions (array of strings), "
        "evidence_used (array of strings)."
    ),
    "technical_debt": (
        "Estimate technical debt from repo scale and maintenance signals. "
        "Scoring hints: stale activity + high issue volume + uneven ownership increases debt. "
        "Return JSON keys: estimated_hours (int), debt_level (low|medium|high|critical), "
        "top_debt_areas (array of strings), rationale (string), assumptions (array of strings), "
        "evidence_used (array of strings)."
    ),
    "security_risk": (
        "Assess security posture conservatively from available repository metadata. "
        "Penalize missing maintenance signals, high stale issue pressure, and low contributor resilience. "
        "Return JSON keys: security_score (int 0-100, higher safer), risk_level (low|medium|high|critical), "
        "critical_findings (array of strings), rationale (string), assumptions (array of strings), "
        "evidence_used (array of strings)."
    ),
    "code_maintainability": (
        "Assess maintainability based on language spread, issue pressure, contributor distribution, and recent activity. "
        "Return JSON keys: maintainability_score (int 0-100), hotspots (array of strings), rationale (string), "
        "assumptions (array of strings), evidence_used (array of strings)."
    ),
    "documentation_quality": (
        "Assess documentation quality from observable metadata only. If docs are not directly observable, "
        "state uncertainty and reduce confidence in rationale. "
        "Return JSON keys: documentation_score (int 0-100), gaps (array of strings), rationale (string), "
        "assumptions (array of strings), evidence_used (array of strings)."
    ),
    "contributor_distribution": (
        "Analyze contributor distribution from top contributors list. "
        "Compute top_contributor_share_percent as the estimated share of top contributor contribution against top-10 sum. "
        "Return JSON keys: distribution_score (int 0-100), top_contributor_share_percent (int), "
        "long_tail_strength (low|medium|high), rationale (string), assumptions (array of strings), "
        "evidence_used (array of strings)."
    ),
    "refactoring_priorities": (
        "Generate risk-weighted refactoring priorities based only on provided repository context. "
        "Prioritize high-impact and high-risk items first. "
        "Return JSON keys: priorities (array of objects with keys title, area, effort_hours, risk, impact, recommendation). "
        "Provide at least 10 items, sorted by priority descending, with realistic effort hours."
    ),
}


def _clip_int(value: Any, min_value: int, max_value: int, default: int) -> int:
    try:
        value_int = int(round(float(value)))
    except Exception:
        return default
    return max(min_value, min(max_value, value_int))


def _clip_float(value: Any, min_value: float, max_value: float, default: float) -> float:
    try:
        value_float = float(value)
    except Exception:
        return default
    return max(min_value, min(max_value, value_float))


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()
    if not text:
        raise AnalysisError("Empty AI response.")

    # Fast path if the model already returned valid JSON only.
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise AnalysisError("AI response did not contain JSON object.")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"Malformed AI JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise AnalysisError("AI response JSON must be an object.")
    return parsed


def _get_grok_api_key() -> str:
    api_key = os.getenv("GROK_API_KEY", "").strip()
    if not api_key:
        raise AnalysisError("Missing GROK_API_KEY environment variable.")
    return api_key


def _make_ai_context(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    contributors = repo_data.get("top_20_contributors", [])
    contributors_trimmed = [
        {"login": c.get("login"), "contributions": c.get("contributions", 0)} for c in contributors[:10]
    ]

    commit_activity = repo_data.get("commit_activity", [])
    last_12_weeks = commit_activity[-12:] if len(commit_activity) > 12 else commit_activity
    commits_last_12_weeks = sum(int(item.get("total_commits", 0)) for item in last_12_weeks)

    return {
        "full_name": repo_data.get("full_name"),
        "description": repo_data.get("description"),
        "visibility": repo_data.get("visibility"),
        "stars": repo_data.get("stars"),
        "forks": repo_data.get("forks_count"),
        "watchers": repo_data.get("watchers"),
        "open_issues": repo_data.get("open_issues"),
        "open_pull_requests": repo_data.get("open_pull_requests"),
        "languages": repo_data.get("languages"),
        "license": repo_data.get("license"),
        "last_commit_date": repo_data.get("last_commit_date"),
        "contributors_total": repo_data.get("contributors"),
        "top_contributors": contributors_trimmed,
        "commits_last_12_weeks": commits_last_12_weeks,
    }


def _grok_chat_json(prompt_key: str, prompt_instruction: str, ai_context: Dict[str, Any]) -> Dict[str, Any]:
    api_key = _get_grok_api_key()

    system_prompt = (
        "You are an expert repository auditor. Return strict JSON only, without markdown, without code fences. "
        "Use only the provided context. Do not invent metrics, files, tools, or vulnerabilities. "
        "If evidence is weak, include explicit assumptions and lower confidence. "
        "Keep scores internally consistent across tasks."
    )
    user_prompt = (
        f"Task: {prompt_key}\n"
        f"Instruction: {prompt_instruction}\n"
        "Repository context JSON:\n"
        f"{json.dumps(ai_context, separators=(',', ':'), ensure_ascii=True)}"
    )

    payload = {
        "model": GROK_MODEL,
        "temperature": 0.2,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout_seconds = 8
    max_retries = 2
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            response_json = response.json()

            choices = response_json.get("choices", [])
            if not choices:
                raise AnalysisError("AI response missing choices.")

            content = choices[0].get("message", {}).get("content", "")
            return _extract_json_object(content)
        except (requests.RequestException, ValueError, AnalysisError) as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(0.6 * (2 ** attempt))
                continue

    raise AnalysisError(f"GROK request failed for {prompt_key}: {last_error}")


def _default_ai_section(task_key: str) -> Dict[str, Any]:
    defaults: Dict[str, Dict[str, Any]] = {
        "repository_health_score": {
            "score": 60,
            "confidence": 0.35,
            "rationale": "Fallback estimate due to unavailable AI output.",
            "positives": [],
            "risks": ["AI response unavailable"],
        },
        "bus_factor": {
            "bus_factor_percent": 50,
            "concentration_risk": "medium",
            "key_person_dependency": [],
            "rationale": "Fallback estimate due to unavailable AI output.",
        },
        "technical_debt": {
            "estimated_hours": 120,
            "debt_level": "medium",
            "top_debt_areas": [],
            "rationale": "Fallback estimate due to unavailable AI output.",
        },
        "security_risk": {
            "security_score": 65,
            "risk_level": "medium",
            "critical_findings": [],
            "rationale": "Fallback estimate due to unavailable AI output.",
        },
        "code_maintainability": {
            "maintainability_score": 62,
            "hotspots": [],
            "rationale": "Fallback estimate due to unavailable AI output.",
        },
        "documentation_quality": {
            "documentation_score": 58,
            "gaps": [],
            "rationale": "Fallback estimate due to unavailable AI output.",
        },
        "contributor_distribution": {
            "distribution_score": 55,
            "top_contributor_share_percent": 35,
            "long_tail_strength": "medium",
            "rationale": "Fallback estimate due to unavailable AI output.",
        },
        "refactoring_priorities": {
            "priorities": [
                {
                    "title": "Reduce module complexity",
                    "area": "core",
                    "effort_hours": 16,
                    "risk": "medium",
                    "impact": "high",
                    "recommendation": "Break large modules into smaller focused units.",
                }
            ],
        },
    }
    return defaults.get(task_key, {"error": "No default available"})


def _normalize_ai_section(task_key: str, raw_section: Dict[str, Any]) -> Dict[str, Any]:
    section = dict(raw_section) if isinstance(raw_section, dict) else {}

    assumptions = section.get("assumptions", [])
    if not isinstance(assumptions, list):
        assumptions = []
    evidence_used = section.get("evidence_used", [])
    if not isinstance(evidence_used, list):
        evidence_used = []

    if task_key == "repository_health_score":
        return {
            "score": _clip_int(section.get("score"), 0, 100, 60),
            "confidence": _clip_float(section.get("confidence"), 0.0, 1.0, 0.5),
            "rationale": str(section.get("rationale", ""))[:1200],
            "positives": section.get("positives", []) if isinstance(section.get("positives", []), list) else [],
            "risks": section.get("risks", []) if isinstance(section.get("risks", []), list) else [],
            "assumptions": assumptions,
            "evidence_used": evidence_used,
        }

    if task_key == "bus_factor":
        return {
            "bus_factor_percent": _clip_int(section.get("bus_factor_percent"), 0, 100, 50),
            "concentration_risk": str(section.get("concentration_risk", "medium")).lower(),
            "key_person_dependency": section.get("key_person_dependency", []) if isinstance(section.get("key_person_dependency", []), list) else [],
            "rationale": str(section.get("rationale", ""))[:1200],
            "assumptions": assumptions,
            "evidence_used": evidence_used,
        }

    if task_key == "technical_debt":
        return {
            "estimated_hours": _clip_int(section.get("estimated_hours"), 0, 20000, 120),
            "debt_level": str(section.get("debt_level", "medium")).lower(),
            "top_debt_areas": section.get("top_debt_areas", []) if isinstance(section.get("top_debt_areas", []), list) else [],
            "rationale": str(section.get("rationale", ""))[:1200],
            "assumptions": assumptions,
            "evidence_used": evidence_used,
        }

    if task_key == "security_risk":
        return {
            "security_score": _clip_int(section.get("security_score"), 0, 100, 65),
            "risk_level": str(section.get("risk_level", "medium")).lower(),
            "critical_findings": section.get("critical_findings", []) if isinstance(section.get("critical_findings", []), list) else [],
            "rationale": str(section.get("rationale", ""))[:1200],
            "assumptions": assumptions,
            "evidence_used": evidence_used,
        }

    if task_key == "code_maintainability":
        return {
            "maintainability_score": _clip_int(section.get("maintainability_score"), 0, 100, 62),
            "hotspots": section.get("hotspots", []) if isinstance(section.get("hotspots", []), list) else [],
            "rationale": str(section.get("rationale", ""))[:1200],
            "assumptions": assumptions,
            "evidence_used": evidence_used,
        }

    if task_key == "documentation_quality":
        return {
            "documentation_score": _clip_int(section.get("documentation_score"), 0, 100, 58),
            "gaps": section.get("gaps", []) if isinstance(section.get("gaps", []), list) else [],
            "rationale": str(section.get("rationale", ""))[:1200],
            "assumptions": assumptions,
            "evidence_used": evidence_used,
        }

    if task_key == "contributor_distribution":
        return {
            "distribution_score": _clip_int(section.get("distribution_score"), 0, 100, 55),
            "top_contributor_share_percent": _clip_int(section.get("top_contributor_share_percent"), 0, 100, 35),
            "long_tail_strength": str(section.get("long_tail_strength", "medium")).lower(),
            "rationale": str(section.get("rationale", ""))[:1200],
            "assumptions": assumptions,
            "evidence_used": evidence_used,
        }

    if task_key == "refactoring_priorities":
        priorities = section.get("priorities", [])
        if not isinstance(priorities, list):
            priorities = []

        normalized_items: List[Dict[str, Any]] = []
        for item in priorities[:25]:
            if not isinstance(item, dict):
                continue
            normalized_items.append(
                {
                    "title": str(item.get("title", "Untitled priority"))[:180],
                    "area": str(item.get("area", "unknown"))[:120],
                    "effort_hours": _clip_int(item.get("effort_hours"), 1, 5000, 8),
                    "risk": str(item.get("risk", "medium")).lower(),
                    "impact": str(item.get("impact", "medium")).lower(),
                    "recommendation": str(item.get("recommendation", ""))[:500],
                }
            )

        if not normalized_items:
            return _default_ai_section("refactoring_priorities")
        return {"priorities": normalized_items}

    return section


def run_ai_analysis(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the 8 GROK prompts and return structured/validated AI output.

    Uses bounded concurrency to keep runtime close to target (~15s).
    """
    ai_context = _make_ai_context(repo_data)
    ai_result: Dict[str, Any] = {}
    failed_tasks: Dict[str, str] = {}
    started_at = time.time()

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(_grok_chat_json, task_key, prompt, ai_context): task_key
            for task_key, prompt in AI_TASKS.items()
        }

        for future in as_completed(future_map):
            task_key = future_map[future]
            try:
                raw_section = future.result()
                ai_result[task_key] = _normalize_ai_section(task_key, raw_section)
            except Exception as exc:
                ai_result[task_key] = _default_ai_section(task_key)
                failed_tasks[task_key] = str(exc)[:300]

    # Ensure every section exists even if some futures unexpectedly failed.
    for task_key in AI_TASKS:
        if task_key not in ai_result:
            ai_result[task_key] = _default_ai_section(task_key)
            failed_tasks[task_key] = "No result produced for task."

    elapsed_ms = int((time.time() - started_at) * 1000)
    fallback_count = len(failed_tasks)
    ai_result["meta"] = {
        "model": GROK_MODEL,
        "elapsed_ms": elapsed_ms,
        "target_runtime_seconds": 15,
        "fallback_count": fallback_count,
        "used_fallback": fallback_count > 0,
        "failed_tasks": failed_tasks,
    }
    return ai_result


def analyze_repository(repo_url: str) -> Dict[str, Any]:
    """
    Full Phase 2 + Phase 3 pipeline.

    Returns structured JSON:
    - repository_data: fetched from GitHub API
    - ai_analysis: output of 8 GROK prompts with normalized schema
    - summary: dashboard-ready key metrics
    """
    pipeline_started = time.time()
    repository_data = collect_repository_data(repo_url)
    ai_analysis = run_ai_analysis(repository_data)

    summary = {
        "health_score": ai_analysis["repository_health_score"]["score"],
        "bus_factor_percent": ai_analysis["bus_factor"]["bus_factor_percent"],
        "technical_debt_hours": ai_analysis["technical_debt"]["estimated_hours"],
        "security_score": ai_analysis["security_risk"]["security_score"],
        "top_5_refactoring_priorities": ai_analysis["refactoring_priorities"].get("priorities", [])[:5],
    }

    return {
        "repository_data": repository_data,
        "ai_analysis": ai_analysis,
        "summary": summary,
        "runtime": {
            "total_elapsed_ms": int((time.time() - pipeline_started) * 1000),
            "target_seconds": 15,
        },
    }


def _parse_repo_url(repo_url: str) -> Tuple[str, str]:
    """Parse GitHub URL and return owner/repository."""
    cleaned = repo_url.strip()
    if not cleaned:
        raise AnalysisError("GitHub URL is required.")

    if cleaned.startswith("git@github.com:"):
        # Handles git@github.com:owner/repo.git
        cleaned = cleaned.replace("git@github.com:", "https://github.com/")

    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"

    parsed = urlparse(cleaned)
    if "github.com" not in parsed.netloc.lower():
        raise AnalysisError("Please provide a valid GitHub repository URL.")

    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]

    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise AnalysisError("Repository URL format must be: https://github.com/owner/repo")

    owner = parts[0]
    repo = parts[1]
    if not re.match(r"^[A-Za-z0-9_.-]+$", owner) or not re.match(r"^[A-Za-z0-9_.-]+$", repo):
        raise AnalysisError("Repository owner/name contains invalid characters.")

    return owner, repo


def _get_github_client() -> Github:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise AnalysisError("Missing GITHUB_TOKEN environment variable.")
    return Github(token, per_page=100)


def _safe_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _estimate_pr_count(client: Github, owner: str, repo: str) -> int:
    # Search API gives a reliable pull request count.
    query = f"repo:{owner}/{repo} is:pr is:open"
    return client.search_issues(query=query).totalCount


def _collect_top_contributors(repo_obj: Any, limit: int = 20) -> List[Dict[str, Any]]:
    contributors = []
    for contributor in repo_obj.get_contributors()[:limit]:
        contributors.append(
            {
                "login": contributor.login,
                "contributions": contributor.contributions,
                "type": contributor.type,
            }
        )
    return contributors


def _collect_commit_activity(repo_obj: Any) -> List[Dict[str, Any]]:
    # GitHub stats endpoint may return None while generating. Retry briefly.
    for _ in range(3):
        weekly = repo_obj.get_stats_commit_activity()
        if weekly is not None:
            return [
                {
                    "week_start_unix": item.week,
                    "total_commits": item.total,
                    "days": item.days,
                }
                for item in weekly
            ]
        time.sleep(1.0)

    return []


def collect_repository_data(repo_url: str) -> Dict[str, Any]:
    """
    Collect non-AI repository data used by RepoGuard AI analysis.

    Returns a normalized dictionary that Phase 3 can feed into GROK prompts.
    """
    owner, repo_name = _parse_repo_url(repo_url)

    try:
        gh = _get_github_client()
        repo_obj = gh.get_repo(f"{owner}/{repo_name}")

        top_contributors = _collect_top_contributors(repo_obj, limit=20)
        commit_activity = _collect_commit_activity(repo_obj)

        contributor_count = repo_obj.get_contributors().totalCount
        open_issues_count = repo_obj.get_issues(state="open").totalCount
        open_pull_requests_count = _estimate_pr_count(gh, owner, repo_name)

        latest_commit = None
        commits = repo_obj.get_commits()
        if commits.totalCount > 0:
            latest_commit = commits[0].commit.committer.date

        data: Dict[str, Any] = {
            "repo_url": repo_url,
            "full_name": repo_obj.full_name,
            "description": repo_obj.description,
            "visibility": "private" if repo_obj.private else "public",
            "stars": repo_obj.stargazers_count,
            "forks": repo_obj.forks,
            "forks_count": repo_obj.forks_count,
            "watchers": repo_obj.watchers_count,
            "open_issues": open_issues_count,
            "open_pull_requests": open_pull_requests_count,
            "languages": repo_obj.get_languages(),
            "default_branch": repo_obj.default_branch,
            "last_commit_date": _safe_iso(latest_commit),
            "license": repo_obj.license.name if repo_obj.license else None,
            "created_at": _safe_iso(repo_obj.created_at),
            "updated_at": _safe_iso(repo_obj.updated_at),
            "pushed_at": _safe_iso(repo_obj.pushed_at),
            "contributors": contributor_count,
            "top_20_contributors": top_contributors,
            "commit_activity": commit_activity,
        }
        return data

    except RateLimitExceededException as exc:
        raise AnalysisError("GitHub API rate limit exceeded. Try again later.") from exc
    except GithubException as exc:
        message = str(exc.data.get("message", "GitHub API request failed.")) if hasattr(exc, "data") and isinstance(exc.data, dict) else str(exc)
        if "Not Found" in message:
            raise AnalysisError("Repository not found or inaccessible.") from exc
        if "Bad credentials" in message:
            raise AnalysisError("Invalid GITHUB_TOKEN credentials.") from exc
        if "Resource not accessible by integration" in message:
            raise AnalysisError("Token does not have access to this repository.") from exc
        raise AnalysisError(f"GitHub API error: {message}") from exc
    except AnalysisError:
        raise
    except Exception as exc:
        raise AnalysisError(f"Unexpected analysis error: {exc}") from exc


if __name__ == "__main__":
    # Quick manual smoke test:
    # export GITHUB_TOKEN=...
    # export GROK_API_KEY=...
    # python analyzer.py https://github.com/facebook/react
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <github_repo_url>")
        raise SystemExit(1)

    output = analyze_repository(sys.argv[1])
    print(json.dumps(output, indent=2))
