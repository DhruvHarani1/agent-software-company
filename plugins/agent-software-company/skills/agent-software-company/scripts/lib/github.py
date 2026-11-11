"""Bounded GitHub CLI reads. Missing/incomplete responses are never empty success."""
import json
import subprocess


class GhError(Exception):
    pass


def gh_json(args, timeout=30):
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True,
                                encoding="utf-8", timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise GhError(f"GitHub read timed out after {timeout}s") from exc
    except OSError as exc:
        raise GhError(f"cannot run GitHub CLI: {exc}") from exc
    if result.returncode:
        raise GhError(f"GitHub CLI failed (exit {result.returncode}); check authentication, access and rate limits")
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise GhError("GitHub returned invalid JSON") from exc


def api_pages(endpoint):
    """Read every REST array page, or fail without returning partial records."""
    if not isinstance(endpoint, str) or not endpoint or endpoint.startswith("-"):
        raise GhError("invalid GitHub endpoint")
    sep = "&" if "?" in endpoint else "?"
    if "per_page=" not in endpoint:
        endpoint += sep + "per_page=100"
    pages = gh_json(["api", endpoint, "--paginate", "--slurp"])
    if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
        raise GhError("GitHub pagination returned an unexpected shape; coverage unavailable")
    if any(not isinstance(item, dict) for page in pages for item in page):
        raise GhError("GitHub pagination contained invalid records; coverage unavailable")
    return [item for page in pages for item in page]
