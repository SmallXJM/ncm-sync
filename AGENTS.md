# Repository Instructions

These instructions apply to the entire repository unless a deeper `AGENTS.md` overrides them.

## Comment Preservation

- Do not remove existing key workflow comments, especially comments that explain important control flow, architecture intent, or maintenance context.
- If a refactor touches code with such comments, preserve them or update them in place so they still match the code.
- Only delete or heavily rewrite these comments when the user explicitly asks for comment cleanup.

## Validation

- Do not run type checks, linters, builds, or other code validation commands after every small edit by default.
- Run validation commands only when the user explicitly asks for checks, or when a change is broad/risky enough that not checking would be irresponsible.

## GitHub Merge Titles

- When creating or finalizing a PR merge title, always include the PR number suffix in the title, using the format `(#<pr_number>)`.
- Example: `feat(cache): add HTTP caching for local music covers (#38)`.
