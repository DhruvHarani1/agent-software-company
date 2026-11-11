#!/usr/bin/env python3
"""List actor-bound claims, read-only. Claims are advisory, not atomic locks.

A trusted local ROSTER.json binds org names to actual GitHub logins. Unknown orgs
are shown as UNVERIFIED and cannot release another actor's work. Releases use
claim_id=<GitHub-comment-id> to target another actor's expired claim explicitly.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from lib.github import GhError, api_pages
from lib.protocol import parse_message, parse_timestamp, validate_message


def load_bindings(path):
    source = Path(path)
    if not source.exists():
        return {}, ["no trusted local roster: all org claims are unverified"]
    try:
        raw = json.loads(source.read_text(encoding="utf-8-sig"))
        bindings = {}
        if not isinstance(raw, dict) or not isinstance(raw.get("orgs"), list):
            raise ValueError("roster needs an orgs array")
        for org in raw["orgs"]:
            if not isinstance(org, dict) or not isinstance(org.get("org"), str):
                raise ValueError("invalid org record")
            names = [org.get("owner_github", ""), *org.get("github_logins", [])]
            if not all(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", name) for name in names):
                raise ValueError("org needs valid owner_github/github_logins")
            if org["org"] in bindings:
                raise ValueError("duplicate org")
            bindings[org["org"]] = {name.casefold() for name in names}
        return bindings, []
    except (OSError, ValueError, TypeError) as exc:
        raise GhError(f"cannot use trusted roster: {exc}") from exc


def evaluate_claims(comments, issue_number, bindings=None, now=None):
    """Reduce immutable comment events without trusting their self-declared actor."""
    bindings = bindings or {}
    now = now or datetime.now(timezone.utc)
    events, active, warnings = [], {}, []
    for comment in comments:
        body = comment.get("body", "")
        msg = parse_message(body)
        if msg is None:
            if isinstance(body, str) and body.lstrip().startswith("[AGENT-MSG"):
                warnings.append(f"comment {comment.get('id', '?')} ignored: " + "; ".join(validate_message(body)))
            continue
        if msg["type"] not in ("claim", "release"):
            continue
        try:
            cid = int(comment["id"])
            actor = comment["user"]["login"].casefold()
            created = parse_timestamp(comment["created_at"])
            if cid <= 0 or not actor or msg["ref"] != f"#{issue_number}":
                raise ValueError("wrong issue reference or actor")
        except (KeyError, TypeError, AttributeError, ValueError):
            warnings.append("claim/release with invalid actor, ID, timestamp or issue reference ignored")
            continue
        org = msg["from"].split("/")[0]
        if org in bindings and actor not in bindings[org]:
            warnings.append(f"comment {cid}: actor {actor} is not registered for {org}; ignored")
            continue
        events.append((created, cid, actor, org, msg))
    for created, cid, actor, org, msg in sorted(events, key=lambda event: (event[0], event[1])):
        trusted = org in bindings and actor in bindings[org]
        target_id = int(msg["attrs"]["claim_id"]) if "claim_id" in msg["attrs"] else None
        target = active.get(target_id) if target_id else next((item for item in active.values()
                          if item["actor"] == actor and item["org"] == org), None)
        if msg["type"] == "claim":
            until = parse_timestamp(msg["attrs"]["lease_until"])
            if not created < until <= created + timedelta(hours=4):
                warnings.append(f"comment {cid}: lease must end after creation and within 4 hours; ignored")
                continue
            if target_id and (target is None or target["actor"] != actor or target["org"] != org):
                warnings.append(f"comment {cid}: renewal does not own target claim; ignored")
                continue
            if target and target["until"] <= created:
                if target_id:
                    warnings.append(f"comment {cid}: expired claim cannot be renewed; post a fresh claim without claim_id; ignored")
                    continue
                # Reacquiring after a lease lapse starts a new queue position.
                # Preserve a competitor's priority earned while this owner was away.
                del active[target["id"]]
                target = None
            root_id = target["id"] if target else cid
            active[root_id] = {"id": root_id, "latest_id": cid, "actor": actor, "org": org,
                "from": msg["from"], "created": target["created"] if target else created,
                "until": until, "verified": trusted}
            if not trusted:
                warnings.append(f"comment {cid}: unverified org/actor; cannot establish exclusive ownership")
        elif target:
            owns = target["actor"] == actor and target["org"] == org
            stale_takeover = bool(target_id and trusted and target["verified"] and target["until"] <= created)
            if owns or stale_takeover:
                del active[target["id"]]
            else:
                warnings.append(f"comment {cid}: release does not own an expired, verified target; ignored")
        elif target_id:
            warnings.append(f"comment {cid}: release target not active")
    rows = sorted(active.values(), key=lambda item: (item["created"], item["id"]))
    for row in rows:
        row["state"] = "UNVERIFIED" if not row["verified"] else "STALE" if row["until"] <= now else "live"
    live = [row for row in rows if row["state"] == "live"]
    if len(live) > 1:
        warnings.append(f"competing live claims: earliest verified event #{live[0]['id']} wins; re-read before editing")
    return rows, warnings


def scan(repo, bindings=None, now=None):
    issues = api_pages(f"repos/{repo}/issues?state=open")
    rows, warnings = [], []
    for issue in issues:
        if "pull_request" in issue:
            continue
        if not isinstance(issue.get("number"), int) or not isinstance(issue.get("title"), str):
            raise GhError("invalid issue record; claim coverage unavailable")
        comments = api_pages(f"repos/{repo}/issues/{issue['number']}/comments")
        found, notes = evaluate_claims(comments, issue["number"], bindings, now)
        for row in found:
            row.update(issue=issue["number"], title=issue["title"])
        rows.extend(found)
        warnings.extend(f"issue #{issue['number']}: {note}" for note in notes)
    return rows, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--roster", default=".agents/ROSTER.json", help="trusted owner-reviewed local actor bindings")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        parser.error("invalid repository")
    try:
        bindings, warnings = load_bindings(args.roster)
        rows, notes = scan(args.repo, bindings)
        warnings.extend(notes)
    except GhError as exc:
        print(f"claims coverage=unavailable: {exc}; ownership unknown", file=sys.stderr)
        return 2
    print("claims coverage=complete for open issues and all comment pages; advisory only")
    for warning in warnings:
        print("WARNING: " + warning)
    for row in rows:
        print(f"#{row['issue']} claim_id={row['id']} {row['state']} {row['from']} actor={row['actor']} until={row['until'].isoformat()} {row['title'][:60]}")
    if not rows:
        print("no valid active claims observed; malformed or unverified events do not establish an all-clear")
    return 0 if not warnings else 2


if __name__ == "__main__":
    sys.exit(main())
