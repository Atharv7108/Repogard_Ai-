import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from github import Github
from github.GithubException import GithubException, RateLimitExceededException


class AnalysisError(Exception):
    """Raised when repository analysis cannot be completed."""


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
    # python analyzer.py https://github.com/facebook/react
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <github_repo_url>")
        raise SystemExit(1)

    output = collect_repository_data(sys.argv[1])
    print(json.dumps(output, indent=2))
