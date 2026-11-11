"""Parse AAP v1 data. A parsed sender is a claim, never authentication."""
import re
from datetime import datetime, timezone

IDENT = r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}"
SENDER = re.compile(rf"{IDENT}/{IDENT}\Z")
RECIPIENT = re.compile(rf"(?:\*|{IDENT}(?:/{IDENT})?|(?:human|login):{IDENT})\Z")
HEADER = re.compile(r"\[AGENT-MSG v1\] type=([a-z-]+) from=(\S+) to=(\S+) ref=(\S+)(.*)\Z")
SHA = re.compile(r"[0-9a-fA-F]{40}\Z")
REQUIRED = {
    "claim": ("Task", "Plan"),
    "release": ("Task", "State left", "Why released"),
    "handover": ("Goal", "Current state", "Confirmed facts", "Next", "Blockers/decisions", "Done means"),
    "question": ("Question", "Why it matters", "Recommendation", "Needed by"),
    "answer": ("Answer", "Source"),
    "review": ("Verdict", "Commit SHA", "Checks", "Red proof", "Problems"),
    "status": ("Doing", "Done", "Blocked", "Next"),
    "decision-request": ("Decision needed", "Options", "Recommendation", "Risk"),
    "hello": ("Who", "How to talk", "Areas we touch", "Trust"),
    "heads-up": ("Touching", "Why", "Overlap", "Proposal"),
}


def parse_timestamp(value: str) -> datetime:
    """Require an ISO-8601 timestamp with offset and normalize it to UTC."""
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("timestamp must include date, time and timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return result.astimezone(timezone.utc)


def _decode(text):
    if not isinstance(text, str) or not text.strip():
        return None, ["empty message"]
    lines = text.strip().splitlines()
    match = HEADER.fullmatch(lines[0])
    if not match:
        return None, ["invalid AAP v1 header"]
    kind, sender, recipient, ref, rest = match.groups()
    errors, attrs = [], {}
    if kind not in REQUIRED:
        errors.append(f"unknown message type: {kind}")
    if not SENDER.fullmatch(sender):
        errors.append("from must be <org>/<agent> using safe identifiers")
    if not all(RECIPIENT.fullmatch(t) for t in recipient.split(",")):
        errors.append("invalid recipient")
    if not re.fullmatch(r"#[1-9][0-9]*|#[A-Za-z][A-Za-z0-9_.-]*|https://[^\s]+", ref):
        errors.append("ref must name an issue, presence reference, or HTTPS URL")
    for field in rest.split():
        if "=" not in field:
            errors.append(f"invalid header attribute: {field}")
            continue
        key, value = field.split("=", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not value or key in attrs:
            errors.append(f"invalid or duplicate attribute: {key}")
        else:
            attrs[key] = value
    body = "\n".join(lines[1:])
    return {"type": kind, "from": sender, "to": recipient, "ref": ref, "attrs": attrs, "body": body}, errors


def validate_message(text: str) -> list[str]:
    msg, errors = _decode(text)
    if msg is None:
        return errors
    kind, attrs, body = msg["type"], msg["attrs"], msg["body"]
    for section in REQUIRED.get(kind, ()):
        if not re.search(rf"^{re.escape(section)}:[ \t]*\S", body, re.M):
            errors.append(f"missing or empty section: {section}:")
    if kind == "claim" and "lease_until" not in attrs:
        errors.append("claim needs lease_until")
    if "lease_until" in attrs:
        try:
            parse_timestamp(attrs["lease_until"])
        except ValueError as exc:
            errors.append(f"lease_until: {exc}")
    if "claim_id" in attrs and not re.fullmatch(r"[1-9][0-9]*", attrs["claim_id"]):
        errors.append("claim_id must be a positive GitHub comment ID")
    if kind in ("review", "handover") or "sha" in attrs:
        if not SHA.fullmatch(attrs.get("sha", "")):
            errors.append("sha must be a full 40-character commit hash")
    if kind == "review":
        verdict = re.search(r"^Verdict:[ \t]*(.*)$", body, re.M)
        if verdict and verdict.group(1).strip() not in ("PASS", "CHANGES"):
            errors.append("Verdict must be PASS or CHANGES")
        body_sha = re.search(r"^Commit SHA:[ \t]*(\S+)[ \t]*$", body, re.M)
        if not body_sha or body_sha.group(1).lower() != attrs.get("sha", "").lower():
            errors.append("Commit SHA must equal header sha")
    return errors


def parse_message(text: str) -> dict | None:
    """Return only known valid messages; callers authenticate the GitHub actor."""
    return None if validate_message(text) else _decode(text)[0]


def addressed(to: str, org: str, agent: str | None = None) -> bool:
    """An org digest includes its agents; an agent inbox includes broadcasts."""
    recipients = [item.strip() for item in to.split(",")]
    return any(item in ("*", org) or item == f"{org}/{agent}" or
               (agent is None and item.startswith(org + "/")) for item in recipients)
