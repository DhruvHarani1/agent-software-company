# agent-software-company

A software-company skill with 80 roles across 18 departments: executive leadership, research, product/design, engineering, platform, independent code review, QA, security, delivery, support and finance. Activate the roles needed for the product and keep work, evidence and resource limits explicit.

## Two editions

- **General company, version 2.0.0:** this repository. Local company ledger, delivery workflows and optional GitHub cross-team coordination.
- **Native subagent company, version 1.0.0:** [agent-software-company-subagents](https://github.com/DhruvHarani1/agent-software-company-subagents). One parent conversation, CEO-selected staffing and real internal native subagents; no user-operated staff chats.

## Existing plugin installation

The marketplace and plugin name/path remain compatible:

```text
/plugin marketplace add DhruvHarani1/agent-software-company
/plugin install agent-software-company@agent-company
```

For plain-folder use, keep [the complete skill directory](plugins/agent-software-company/skills/agent-software-company) together and make its SKILL.md available through your host's skill mechanism. Python helpers require Python 3.10+ and no additional packages. GitHub helpers additionally require gh and authorized repository reads.

Start with an outcome such as: "Use the software-company skill to understand this product and organize its next delivery milestone."

## Current behavior and compatibility

The [skill entrypoint](plugins/agent-software-company/skills/agent-software-company/SKILL.md) routes to role, company, safety and delivery guidance. Local company records do not launch workers or authenticate evidence; the host's actual tools perform the work. Roles and tokens do not grant action authority.

Version 2.0.0 changes inbox behavior to non-consuming peek by default, with explicit --ack; skill updates use reviewed immutable candidates rather than pull --apply. Read [the changelog](CHANGELOG.md) before changing existing automation. Legacy project-profile/org references and org_profile.py from 1.4 remain available; the new ledger does not automatically migrate or synchronize their records.

## Verification

From `plugins/agent-software-company/skills/agent-software-company`, run:

```text
python -B -m unittest discover -s tests -v
```

Tests use isolated fixtures and mocked GitHub reads. Validation was performed on Windows; a real symlink test can skip without OS privilege. Production behavior, other operating systems, and external provider permissions require their own verification.

## License

[MIT](LICENSE)
