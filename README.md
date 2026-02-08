# Generic Prompt Lab: Excel → CSV → Model JSON

This repository contains a **vendor-agnostic prompt lab** for validating multi-agent
LLM prompts. It converts a synthetic Excel workbook into CSV artifacts, loads those
CSV files, runs two agents that emit JSON fragments, validates each fragment, and
assembles a minimal generic model JSON.

**Privacy note:** All sample data is synthetic and generic. No proprietary schemas,
models, or business logic are included.

## Quickstart

```bash
python3 -m pip install -r requirements.txt
python3 -m prompt_lab
```

The command will:

1. Create a synthetic workbook at `data/sample_workbook.xlsx` (if missing)
2. Convert the workbook into CSV artifacts under `out/artifacts/<run_id>/`
3. Run the agents (mocked by default)
4. Validate outputs and assemble the final model JSON
5. Save a run report under `out/run_<run_id>.json`

## CSV Artifacts

The conversion step creates explicit CSV files:

### `inputs.csv`

Derived from sheet named `Inputs`.

```
key,value
BaseRate,0.05
Volume,1200
```

### `formulas.csv`

Derived from a sheet named `Formulas` if present, otherwise extracted from formula
cells across the workbook.

```
name,formula,source_sheet,cell
AdjustedRate,=BaseRate+Adjustment,Formulas,B2
```

### `table_<sheet>.csv`

Each non-input, non-formula sheet with numeric data is exported as a table CSV.
The sheet name becomes the table name.

## Environment Flags

By default the harness uses a deterministic mock LLM output. To enable real LLM
calls, set:

```bash
export USE_REAL_LLM=true
export OPENAI_API_KEY=...
export LLM_MODEL=...
```

## Output Model Shape

The assembled model JSON follows this structure:

```json
{
  "inputs": [],
  "tables": [],
  "calculations": []
}
```

## Notes

- Python 3.11
- Excel parsing: `openpyxl`
- CSV parsing/writing: Python `csv` module
- Validation: `jsonschema`