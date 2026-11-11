#!/usr/bin/env python3
"""Read complete agent messages without implicitly consuming them.

Default: peek at pending messages. --ack acknowledges after successful retrieval
and full output. --since ISO replays without changing state; --no-save explicitly
selects peek mode. State is scoped by repo/org/recipient under .agents-state/inbox,
not the legacy org.last cursor. This command never writes to GitHub.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone

from lib.github import GhError, api_pages
from lib.protocol import addressed, parse_message, parse_timestamp, validate_message


EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
OVERLAP = timedelta(minutes=2)
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")


class InboxError(Exception):
    pass


def utc_now():
    return datetime.now(timezone.utc)


def timestamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def checked_identifier(value, label):
    if not IDENTIFIER.fullmatch(value):
        raise InboxError(f"invalid {label}: use 1-100 letters, digits, dots, underscores, or hyphens, starting with a letter or digit")
    return value


def make_scope(repo, org, agent):
    parts = repo.split("/")
    if len(parts) != 2:
        raise InboxError("invalid repo: expected owner/name")
    for part in parts:
        checked_identifier(part, "repository identifier")
    checked_identifier(org, "org")
    if agent is not None:
        checked_identifier(agent, "agent")
    if len(org) > 64 or (agent is not None and len(agent) > 64):
        raise InboxError("org and agent must fit AAP identifiers (at most 64 characters)")
    return {"repo": repo.lower(), "org": org, "agent": agent}


def state_path(state_dir, scope):
    root = (Path(state_dir) / "inbox").resolve()
    key = hashlib.sha256(json.dumps(scope, sort_keys=True).encode("utf-8")).hexdigest()
    path = root / (key + ".json")
    if path.resolve().parent != root:
        raise InboxError("state path resolves outside its configured directory")
    return path


def load_state(path, scope):
    if not path.exists():
        return {"version": 1, "scope": scope, "cursor": timestamp(EPOCH), "seen": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1 or data.get("scope") != scope:
            raise ValueError("unsupported version or scope mismatch")
        parse_timestamp(data["cursor"])
        if not isinstance(data["seen"], dict):
            raise ValueError("seen must be an object")
        for comment_id, version in data["seen"].items():
            if not comment_id.isdigit() or int(comment_id) < 1 or not isinstance(version, dict):
                raise ValueError("invalid acknowledged comment")
            parse_timestamp(version["updated_at"])
            if not re.fullmatch(r"[0-9a-f]{64}", version["digest"]):
                raise ValueError("invalid acknowledged content digest")
        return data
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise InboxError(f"cannot read inbox state {path}: {exc}; restore or move the file explicitly; state was not reset") from exc


def save_state(path, data):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=path.stem + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def collect_messages(comments, scope, seen, replay=False):
    candidates, warnings = {}, []
    for comment in comments:
        try:
            if not isinstance(comment, dict) or type(comment.get("id")) is not int or comment["id"] < 1:
                raise ValueError("missing positive numeric id")
            body = comment.get("body")
            if body is None:
                body = ""
            if not isinstance(body, str):
                raise ValueError("body is not text")
            updated = parse_timestamp(comment["updated_at"])
            created = parse_timestamp(comment["created_at"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InboxError(f"invalid GitHub comment response: {exc}; nothing acknowledged") from exc
        message = parse_message(body)
        if message is None:
            if body.lstrip().startswith("[AGENT-MSG"):
                warnings.append(f"Ignored invalid/unsupported protocol comment {comment['id']}: "
                                + "; ".join(validate_message(body)))
            continue
        if not addressed(message["to"], scope["org"], scope["agent"]):
            continue
        if scope["agent"] and message["from"] == f"{scope['org']}/{scope['agent']}":
            continue
        version = {"updated_at": timestamp(updated),
                   "digest": hashlib.sha256(body.encode("utf-8")).hexdigest()}
        previous = candidates.get(comment["id"])
        if previous is None or updated >= previous["updated"]:
            candidates[comment["id"]] = {"id": comment["id"], "updated": updated, "created": created,
                                          "body": body, "url": comment.get("html_url", ""), "version": version}
    messages = [item for item in candidates.values()
                if replay or seen.get(str(item["id"])) != item["version"]]
    messages.sort(key=lambda item: (item["updated"], item["id"]))
    return messages, warnings


def run(args, stdout=None, stderr=None):
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    if args.ack and args.since:
        raise InboxError("--since is replay-only and cannot be combined with --ack")
    scope = make_scope(args.repo, args.org, args.agent)
    path = state_path(args.state_dir, scope)
    lock = path.with_suffix(".lock")
    locked = False
    try:
        if args.ack:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise InboxError(f"inbox acknowledgement already locked: {lock}; if a prior process crashed, confirm it has stopped before removing its lock") from exc
            locked = True
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(f"pid={os.getpid()}\n")
        state = load_state(path, scope)
        legacy = Path(args.state_dir) / (scope["org"] + ".last")
        if legacy.exists() and not path.exists():
            stderr.write(f"Legacy cursor {legacy} is not used: it cannot safely identify repository/recipient delivery. Starting new scoped state; use --since for a read-only replay.\n")
        # Local time is only a ceiling, never proof of the server's read position.
        # In particular an idle read must not move a cursor to an ahead local clock.
        boundary = utc_now()
        cursor = parse_timestamp(state["cursor"])
        since = parse_timestamp(args.since) if args.since else max(EPOCH, cursor - OVERLAP)
        endpoint = f"repos/{scope['repo']}/issues/comments?since={timestamp(since)}&per_page=100"
        comments = api_pages(endpoint)
        messages, warnings = collect_messages(comments, scope, state["seen"], replay=bool(args.since))
        for warning in warnings:
            stderr.write(warning + "\n")
        for message in messages:
            stdout.write(f"--- comment {message['id']} updated={timestamp(message['updated'])} {message['url']} ---\n")
            stdout.write(message["body"] + "\n\n")
        if not messages:
            stdout.write(f"No pending messages in this scoped inbox since {timestamp(since)}.\n")
        if not args.ack:
            stdout.write("Peek/replay only: nothing acknowledged. Use --ack to display and acknowledge pending messages.\n")
        else:
            stdout.write(f"Displayed {len(messages)} message version(s); acknowledgment will be saved after successful output to {path}.\n")
        # A failed/broken output must not consume any messages or advance the cursor.
        stderr.flush()
        stdout.flush()
        if args.ack:
            observed = max((parse_timestamp(comment["updated_at"]) for comment in comments), default=None)
            # Timestamp fields were validated before output. Keep the old cursor on
            # empty reads and when a skewed/changed local clock is behind it.
            watermark = cursor if observed is None else max(cursor, min(boundary, observed))
            seen = dict(state["seen"])
            for message in messages:
                seen[str(message["id"])] = message["version"]
            lower_bound = max(EPOCH, watermark - OVERLAP)
            seen = {key: value for key, value in seen.items()
                    if parse_timestamp(value["updated_at"]) >= lower_bound}
            save_state(path, {"version": 1, "scope": scope, "cursor": timestamp(watermark), "seen": seen})
        return messages
    finally:
        if locked:
            lock.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--org", required=True)
    parser.add_argument("--agent")
    parser.add_argument("--since", help="UTC/offset timestamp for read-only replay; cannot be used with --ack")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--ack", action="store_true", help="display full pending messages and acknowledge after successful output")
    mode.add_argument("--no-save", action="store_true", help="explicit peek mode (the default)")
    parser.add_argument("--state-dir", default=".agents-state")
    args = parser.parse_args(argv)
    if args.ack and args.since:
        parser.error("--since is replay-only and cannot be combined with --ack")
    try:
        run(args)
    except (InboxError, GhError, OSError, ValueError) as exc:
        print(f"inbox error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
