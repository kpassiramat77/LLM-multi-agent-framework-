from typing import Any, Dict, List


def build_agent_prompts(csv_texts: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    tables_block = format_tables_block(csv_texts.get("tables", []))
    return {
        "model_builder": {
            "system": SYSTEM_MODEL_BUILDER,
            "user": USER_MODEL_BUILDER.format(
                inputs_csv=format_csv_block(csv_texts["inputs"]),
                tables_csv=tables_block,
            ),
        },
        "formula_calculation": {
            "system": SYSTEM_FORMULA_CALC,
            "user": USER_FORMULA_CALC.format(
                formulas_csv=format_csv_block(csv_texts["formulas"])
            ),
        },
    }


def format_tables_block(tables: List[Dict[str, str]]) -> str:
    if not tables:
        return "No table CSVs were provided."
    blocks = []
    for table in tables:
        blocks.append(
            f"{table['filename']} (table name: {table['name']}):\n{table['content']}"
        )
    return "\n\n".join(blocks)


def format_csv_block(item: Dict[str, str]) -> str:
    return f"{item['filename']}:\n{item['content']}"


SYSTEM_MODEL_BUILDER = (
    "You are the Model Builder Agent. Return JSON only with keys "
    '"inputs" and "tables". Do not include calculations.'
)

USER_MODEL_BUILDER = """Use the CSV artifacts below to build inputs and tables.

Rules:
- Return JSON only.
- Use only input keys and table names present in the CSVs.
- Do not invent new inputs or tables.
- Follow this output shape:
  {{
    "inputs": [{{"name": "string", "value": 0}}],
    "tables": [{{"name": "string", "columns": ["col"], "rows": [[0]]}}]
  }}

CSV artifacts:
{inputs_csv}

{tables_csv}
"""

SYSTEM_FORMULA_CALC = (
    "You are the Formula Calculation Agent. Return JSON only with key "
    '"calculations". Do not include inputs or tables.'
)

USER_FORMULA_CALC = """Use the CSV artifact below to build calculations.

Rules:
- Return JSON only.
- Use only references that appear in the inputs or table names.
- Do not invent new input or table names.
- Follow this output shape:
  {{
    "calculations": [
      {{"name": "string", "expression": "string", "references": ["name"]}}
    ]
  }}

CSV artifact:
{formulas_csv}
"""
