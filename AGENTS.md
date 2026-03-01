# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

This is a Python-based **Generic Prompt Lab** that converts Excel workbooks into CSV artifacts, runs multi-agent LLM prompts (Orchestrator + Model Builder + Formula Calculation agents), validates outputs, and assembles a model JSON. See `README.md` for full documentation.

### Running the application

```bash
python3 -m prompt_lab
```

By default the application uses **mock LLM output** (deterministic, no API key needed). To use real LLM calls, set `USE_REAL_LLM=true`, `OPENAI_API_KEY`, and optionally `LLM_MODEL`.

### Linting

```bash
flake8 prompt_lab/ --max-line-length=100
```

Pyright reports pre-existing `reportOptionalMemberAccess` / `reportOptionalSubscript` errors in `csv_artifacts.py`, `llm_client.py`, and `sample_workbook.py` due to openpyxl's type stubs. These are known and not regressions.

### Testing

No automated test suite exists yet. Verify correctness by running the application (`python3 -m prompt_lab`) and confirming the scorecard shows `Overall: PASS`.

### Key gotchas

- The `out/` and `data/` directories are created automatically on first run; they are not checked into git.
- Dependencies install to `~/.local` (user site-packages). Ensure `~/.local/bin` is on `PATH` for CLI tools like `flake8`.
- Python 3.12 works fine despite README stating 3.11.
