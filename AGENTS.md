# AGENTS.md

This file provides guidance to agentic AI tools (Claude Code, ChatGPT Codex, etc.) when working with code in this repository.

## Commands

### Setup

### Documentation

Documentation lives in `docs/` apart from `AGENTS.md` and `README.md` that live in the root of the repo. Documentation includes `backlog.md` with list of bugs and future functionality, `changelog.md` with introduced changes, and specifications files.
Keep `README.md` brief and clear - it is for carbon-based life-forms with short attention span. Put in there only the information a user might need to understand what the repo is for, how to use it, what are the common use cases. Use examples, if appropriate. Architectural details, rarely used features, advanced usage belong to `docs/`.

### Workflow

Before starting to implement new feature or a refactoring, ask the user whether you should create a new branch for it. At the end of the round of changes, ask whether the branch should be merged to main (or to some other branch).
Before editing the code, perform `git pull`. 
After implementing a new feature or doing a major refactoring:
 - Add changes to `docs/changelog.md`.
 - If these features or bugs were mentioned in docs/backlog.md, move their description from there to docs/changelog.md and remove them from the backlog.
- Re-read `README.md` and `AGENTS.md`, update to reflect recent changes.
- Update `pyproject.toml` or `requirements.txt`, if present.
- Run the tests, if present.
- At the end of the round of changes, ask whether the branch should be merged to `main` (or to some other branch).
- After each round of editing the code, commit the changes to git and run `git push`.