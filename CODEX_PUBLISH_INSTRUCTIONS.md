# Instructions for Codex: publish this folder as a GitHub public repository

Recommended repository name: **TCM-SD42-Model-Comparison**

## Hard constraints

1. Upload **only the contents of this folder**. Do not search parent directories for extra files.
2. Keep the repository **Public** only after confirming no additional files were introduced.
3. Do not add raw TCM-SD JSON records, predictions, model weights, LoRA adapters, logs, `.env` files, API keys, or AutoDL paths.
4. Do not add the full manuscript DOCX/MD unless explicitly instructed later.
5. Do not change reported numerical results.
6. Keep the provenance statement that TCM-SD42 is a TCM-SD-derived 42-class task and **not a direct 42-label subset of the official normalized 148-class taxonomy**.
7. Run the checks below before the first push.

## Pre-push checks

```bash
python code/parser_tests.py
grep -RInE '(/root/|/autodl|sk-[A-Za-z0-9]|api[_-]?key|password|secret)' . --exclude=CODEX_PUBLISH_INSTRUCTIONS.md || true
find . -type f -size +20M -print
```

Expected: parser tests pass; no private-path/secret hits in repository content; no file >20 MB.

## Suggested Git commands

```bash
git init
git branch -M main
git add .
git commit -m "Initial public reproducibility release"
# Create a new public GitHub repository named TCM-SD42-Model-Comparison, then:
git remote add origin <NEW_REPOSITORY_GIT_URL>
git push -u origin main
```

After push, report the final repository URL and the commit SHA.
