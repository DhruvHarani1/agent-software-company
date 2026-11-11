# Clear, compact coordination

Prefer short agent messages with exact facts: task, revision, result, blocker and next action. Preserve full hashes, commands, error text, quantities and uncertainty. Code, quotations, public release notes, and decisions for humans should remain natural and clear.

A compact report can be:

```text
CHANGES sha=<full40> regression 8/8 pass; integration not run. Missing forbidden-role case at src/access.py:42. Next: add case, rerun affected checks.
```

The line is a report example, not a valid AAP message by itself. Protocol messages need the exact required header/sections; see [templates](../templates/messages.md).

Use lists or tables when they make parallel facts easier to compare. Do not mechanically delete articles or force fragments when that hides causality, risk, or ownership. A necessary long security explanation is preferable to a misleading short verdict. Lint style suggestions are warnings, never authorization or correctness gates.

Write owner decisions, approval requests, destructive actions, financial effects and production risks in plain sentences. Identify the concrete action and its effect. Do not compress a scoped authorization into an ambiguous PASS/approved token.

There is no requirement to install a separate terse-style plugin. The skill makes no fixed percentage savings claim. Measure actual cost and rework where the runtime exposes them; clarity and reliable evidence take priority.
