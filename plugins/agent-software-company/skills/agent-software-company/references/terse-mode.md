# Terse mode (built in): fewer tokens between agents

The skill ships its own compact style (inspired by the "caveman" style plugin). Use it for ALL agent-to-agent text: briefs, standups, reviews, handovers, status lines, issue comments. If a "caveman" plugin or similar terse skill is installed, follow it; if not, follow this file.

## Rules

- Drop articles (a, an, the), filler (just, really, basically, simply, actually), pleasantries and hedging. Fragments are fine.
- Short words: "fix", not "implement a solution for". Keep technical terms exact.
- Pattern: `<thing> <action> <reason>. <next step>.`
- Numbers, SHAs, file:line, commands and exact error text stay as they are. Code blocks unchanged.
- Lists and tables over paragraphs. One message, one purpose.
- Message headers and section names stay exact (they are the protocol).

## NOT terse (write normally)

Code, commit messages, pull request titles users may read, release notes for end users, security warnings, destructive or irreversible actions (backups, migrations, production data), and anything the human owner must decide: write those in clear plain language so nothing is misread. Resume terse mode afterwards.

## Levels

| Level | Use |
|---|---|
| lite | Reports to the human owner: plain sentences, no filler, decisions first |
| full (default) | Agent to agent |
| ultra | Status lines and review comments: `PASS sha=abc123 tsc ok tests 142/142 red 5/5 risk low` |

## Examples

Not terse: "I have reviewed the pull request and I found that the tests all pass, but the release note is missing."
Terse: `CHANGES. 142/142 pass. red proof ok. release note missing (unreleased list).`

Not terse: "I would like to ask whether the other team is planning to modify the same file."
Terse: `question: you touching server/config/org.ts? I need it for #88. rec: you go first, I wait. need by: today.`

## Hygiene

- The human owner's reports: terse inside, but always the same top-down order: decisions needed, what changed, what failed, what is next.
- Never compress a quoted error, a command that was run, or a number.
