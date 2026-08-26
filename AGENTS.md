# AGENTS.md

This file provides guidance to agentic AI tools (Claude Code, ChatGPT Codex, etc.) when working with code in this repository.

## Commands

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Documentation

Documentation lives in `docs/` apart from `AGENTS.md` and `README.md` that live in the root of the repo. Documentation includes `backlog.md` with list of bugs and future functionality, `changelog.md` with introduced changes, and specifications files.

### Workflow

After implementing a new feature or doing a major refactoring:
- add changes to `changelog.md`. 
- If these features or bugs were mentioned in the `backlog.md`, move their description from there to the `changelog.md` and remove them from the `backlog.md`. 

Before starting to implement new feature or a refactoring, ask the user whether you should create a new branch for it. At the end of the round of changes, ask whether the branch should be merged to main (or to some other branch).
Before editing the code, perform `git pull`. 
After each round of editing the code, commit the changes to git and run `git push`.