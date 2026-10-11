import os
import re
import httpx
from rich import print
from langchain.tools import tool


BASE_URL = "https://api.github.com"
MAX_FILES = 100
MAX_PATCH_CHARS = 1500


def parse_github_url(url: str) -> tuple[str, str, str, int]:
    """'https://github.com/o/r/pull/12' -> ('o', 'r', 'pull', 12)"""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/(pull|issues)/(\d+)", url.strip())
    if not m:
        raise ValueError("Expected a GitHub PR or issue URL")
    owner, repo, kind, number = m.groups()
    return owner, repo, kind, int(number)



def _github_get(path: str):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = httpx.get(f"{BASE_URL}{path}", headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


@tool
def get_issue(owner: str, repo: str, number: int) -> str:
    """Fetch a GitHub issue: title, description, labels and the first few comments."""
    try:
        issue = _github_get(path=f"/repos/{owner}/{repo}/issues/{number}")
        comment = _github_get(path=f"/repos/{owner}/{repo}/issues/{number}/comments?per_page=5")
    except httpx.HTTPError as e:
        return f"GitHub request failed: {e}"

    labels = ", ".join([label['name'] for label in issue['labels']])
    parts = [
        f"Title: {issue['title']}",
        f"Author: {issue['user']['login']}",
        f"labels: {labels}",
        f"Descriptions: {issue['body']}"
    ]
    for c in comment:
        parts.append(f"\nComment by {c['user']['login']}: {c['body'][:500]}")
    return "\n".join(parts)


@tool
def get_pull_request(owner: str, repo: str, number: int) -> str:
    """Fetch a Github PR: title, descriptions and the files with diff"""
    try:
        pr = _github_get(path=f"/repos/{owner}/{repo}/pulls/{number}")
        files = _github_get(f"/repos/{owner}/{repo}/pulls/{number}/files?per_page={MAX_FILES}")
    except httpx.HTTPError as e:
        return f"GitHub request failed: {e}"

    parts = [
        f"Title: {pr['title']}",
        f"Author: {pr['user']['login']}",
        f"Descriptions: {pr.get('body') or '(None)'}",
        f"Changed files: {pr['changed_files']} (+{pr['additions']} / -{pr['deletions']})"
    ]

    for f in files:
        patch = (f.get("patch") or "(no diff available)")[:MAX_PATCH_CHARS]
        parts.append(f"\n--- {f['filename']} ({f['status']})\n{patch}")
    return "\n".join(parts)