# Token economy: get the same quality for far fewer tokens

1. **Write once, read many.** Keep area notes (`docs/team/<area>.md`), the standup comment and decision files current. A new session reads those instead of replaying history or re-reading the codebase.
2. **Fresh context for isolated work, fork only when the task depends on the conversation.** A fixer needs the issue, the plan and the files, not the Boss's whole chat.
3. **Read diffs, not trees.** Reviewers read `gh pr diff` and the touched files, not the repository. Incremental review: if only one file changed since the last verdict, re-run only what it affects and say so (the verdict names the SHA).
4. **Cache verdicts by SHA.** If the head SHA is the same as a previous PASS, do not re-run: link the verdict.
5. **Right model for the role.** Read-only roles (inventory, route tables, listings, lint-type checks) can use a smaller, cheaper model; keep the strongest model for design, security reasoning and risky reviews.
6. **Cap output.** Max findings per tester, max pull requests per manager per turn, tables instead of prose, counts instead of logs. Never paste long logs: attach the last 20 relevant lines and the counts.
7. **Edit, do not repost.** Standups, claims renewals and status are ONE living comment edited each turn.
8. **Batch questions.** One `decision-request` with options and a recommendation beats five round trips.
9. **Avoid duplicate work.** Search issues and open pull requests before starting (`gh issue list --search`), claim before building, one owner per issue.
10. **Do not poll.** One inbox read per turn; end the turn when waiting; the harness wakes you when a session finishes.
11. **Run the cheap check first.** Type-check before the full suite, targeted tests before the full suite, full suite once per batch.
12. **Terse mode** for all agent text (terse-mode.md): typically 40-70% fewer words.
13. **Concurrency is a cost.** Two sessions at a time avoids both rate limits and slow machines; a usage limit stops every session at once.
14. **Park, do not drag.** If a task is blocked for a decision, release the claim, write the handover, and take another task instead of idling in a long session.
15. **Measure.** Each sprint record: pull requests per cost unit (sessions or tokens if visible), re-reviews caused by missing checks, duplicated work found. Fix the biggest waste first.
