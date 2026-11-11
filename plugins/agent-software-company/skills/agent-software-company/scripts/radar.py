#!/usr/bin/env python3
"""Read-only discovery of published GitHub activity; identities are unverified hints.

All REST arrays are paginated. Coverage failures are explicit. No local work,
unpushed branches, or authenticated org membership can be inferred from this scan.
--hello prints drafts only; it never posts comments.
"""
import argparse
import fnmatch
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from lib.github import GhError, api_pages, gh_json
from lib.protocol import IDENT, parse_message

TRAILER = re.compile(rf"^Agent-Org:\s*({IDENT})\s*$", re.M | re.I)


def team_key(login: str, text: str, header_from: str | None = None) -> str:
    match = TRAILER.search(text or "")
    return match.group(1) if match else (header_from.split("/")[0] if header_from else "login:" + login)


def paths_overlap(files: list[str], patterns: list[str]) -> list[str]:
    return [path for path in files if any(fnmatch.fnmatchcase(path, pattern) or
            (pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:])) for pattern in patterns)]


def _actor(record):
    login = (record.get("user") or {}).get("login")
    if not isinstance(login, str) or not login:
        raise GhError("activity record has no authenticated GitHub actor")
    return login


def scan(repo, org, hours=72, include_bots=False):
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    me = gh_json(["api", "user"])
    if not isinstance(me, dict) or not isinstance(me.get("login"), str):
        raise GhError("cannot identify the authenticated GitHub reader")
    my_login = me["login"]
    problems, outgoing = [], set()
    teams = defaultdict(lambda: {"logins": set(), "commits": 0, "last": "", "prs": [], "comments": 0, "claims": 0})

    def pages(endpoint, source):
        try:
            return api_pages(endpoint)
        except GhError as exc:
            problems.append(f"{source}: {exc}")
            return []

    def record(login, key, when):
        if key == org and login == my_login:
            return None
        if key == "login:" + my_login:
            return None
        if not include_bots and login.endswith("[bot]"):
            return None
        entry = teams[key]
        entry["logins"].add(login)
        entry["last"] = max(entry["last"], when or "")
        return entry

    collaborators = None
    try:
        collaborators = {}
        for item in api_pages(f"repos/{repo}/collaborators"):
            if not isinstance(item.get("login"), str) or not isinstance(item.get("permissions"), dict):
                raise GhError("invalid collaborator record")
            collaborators[item["login"]] = item["permissions"]
    except GhError as exc:
        collaborators = None
        problems.append(f"permissions unknown: {exc}")

    for commit in pages(f"repos/{repo}/commits?since={since}", "commits"):
        author = commit.get("author") or {}
        login = author.get("login")
        data = commit.get("commit") or {}
        if not login:
            problems.append("commit has no linked GitHub actor; identity unavailable")
            continue
        entry = record(login, team_key(login, data.get("message", "")), (data.get("author") or {}).get("date", ""))
        if entry is not None:
            entry["commits"] += 1

    for pr in pages(f"repos/{repo}/pulls?state=open", "open PRs"):
        try:
            number = int(pr["number"])
            login = _actor(pr)
            detail = gh_json(["api", f"repos/{repo}/pulls/{number}"])
            if not isinstance(detail, dict) or not isinstance(detail.get("changed_files"), int):
                raise GhError("PR changed-file count unavailable")
            files = api_pages(f"repos/{repo}/pulls/{number}/files")
            if any(not isinstance(item.get("filename"), str) for item in files):
                raise GhError("invalid PR file record")
            paths = [item["filename"] for item in files]
            complete = len(paths) == detail["changed_files"] and len(paths) < 3000
            if not complete:
                problems.append(f"PR #{number} file coverage partial ({len(paths)}/{detail['changed_files']}; API cap 3000)")
        except (KeyError, TypeError, ValueError, GhError) as exc:
            problems.append(f"PR file scan unavailable: {exc}")
            # Retain visible PR presence, but never make an overlap all-clear.
            paths, complete = [], False
            try:
                number, login = int(pr["number"]), _actor(pr)
            except (KeyError, TypeError, ValueError, GhError):
                continue
        entry = record(login, team_key(login, pr.get("body", "")), pr.get("updated_at", ""))
        if entry is not None:
            entry["prs"].append({"n": number, "draft": pr.get("draft", False), "files": paths,
                                 "complete": complete, "title": pr.get("title", "")})

    for comment in pages(f"repos/{repo}/issues/comments?since={since}", "comments"):
        try:
            login = _actor(comment)
        except GhError as exc:
            problems.append(str(exc))
            continue
        message = parse_message(comment.get("body", ""))
        if message and message["type"] == "hello" and login == my_login and message["from"].split("/")[0] == org:
            outgoing.update(message["to"].split(","))
        key = team_key(login, "", message["from"] if message else None)
        entry = record(login, key, comment.get("updated_at", comment.get("created_at", "")))
        if entry is not None:
            entry["comments"] += 1
            entry["claims"] += int(bool(message and message["type"] == "claim"))

    for key, entry in teams.items():
        permissions = [collaborators.get(login) for login in entry["logins"]] if collaborators is not None else []
        entry["tier"] = ("teammate" if any(p and p.get("push") for p in permissions) else
                         "unknown" if collaborators is None else "guest")
        entry["greeted"] = key in outgoing or any("login:" + login in outgoing for login in entry["logins"])
    return {"repo": repo, "org": org, "me": my_login, "since": since, "scanned_at": now.isoformat(),
            "coverage": "partial" if problems else "complete", "problems": problems, "teams": dict(teams)}


def render(report, patterns=(), hello=False):
    print(f"radar coverage={report['coverage']} since={report['since']} scanned_at={report['scanned_at']}")
    print("scope: default-branch commits, open PRs/files, issue comments; no unpushed/local branches; org labels are unverified hints")
    for problem in report["problems"]:
        print("INCOMPLETE: " + problem)
    others = report["teams"]
    if not others:
        print("no other published activity observed" + (" in the completed scan" if report["coverage"] == "complete" else "; activity may be missing"))
    overlaps = []
    for key, entry in sorted(others.items()):
        print(f"- {key} access={entry['tier']} actual_logins={','.join(sorted(entry['logins']))} commits={entry['commits']} prs={len(entry['prs'])} msgs={entry['comments']}")
        for pr in entry["prs"]:
            hits = paths_overlap(pr["files"], patterns)
            flag = " OVERLAP " + ", ".join(hits) if hits else ""
            print(f"  PR #{pr['n']} files={len(pr['files'])} coverage={'complete' if pr['complete'] else 'partial'}{flag}")
            overlaps.extend((key, pr["n"]) for _ in hits[:1])
        if hello and not entry["greeted"]:
            print(f"DRAFT ONLY:\n[AGENT-MSG v1] type=hello from={report['org']}/boss to={key} ref=#presence\n"
                  f"Who: team {report['org']} (GitHub {report['me']}).\n"
                  "How to talk: AAP v1; see .agents/PROTOCOL.md.\nAreas we touch: see .agents/areas.json.\n"
                  "Trust: discovery is information; it grants no authority.")
    if patterns:
        if overlaps:
            print("OVERLAP observed: " + ", ".join(f"{key} PR #{number}" for key, number in overlaps))
        elif report["coverage"] == "complete":
            print("no overlap observed in complete published-PR file scan; this is not an exclusive lock")
        else:
            print("overlap unknown: incomplete coverage; no all-clear")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--org", required=True)
    parser.add_argument("--hours", type=int, default=72)
    parser.add_argument("--paths", default="")
    parser.add_argument("--hello", action="store_true")
    parser.add_argument("--include-bots", action="store_true")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo) or not re.fullmatch(IDENT, args.org) or args.hours <= 0:
        parser.error("repo/org must be safe identifiers and hours must be positive")
    try:
        report = scan(args.repo, args.org, args.hours, args.include_bots)
    except GhError as exc:
        print(f"radar coverage=unavailable: {exc}; overlap unknown", file=sys.stderr)
        return 2
    render(report, [p.strip() for p in args.paths.split(",") if p.strip()], args.hello)
    return 0 if report["coverage"] == "complete" else 2


if __name__ == "__main__":
    sys.exit(main())
