import os
from typing import Any, Dict, List


def build_orchestrator_prompt(csv_manifest: Dict[str, Any]) -> Dict[str, str]:
    inputs_file = os.path.basename(csv_manifest["inputs_csv"])
    formulas_file = os.path.basename(csv_manifest["formulas_csv"])
    tables = csv_manifest.get("tables", [])
    if tables:
        table_lines = [
            f"- {item['name']}: {os.path.basename(item['path'])}" for item in tables
        ]
        tables_block = "\n".join(table_lines)
    else:
        tables_block = "None"
    return {
        "system": SYSTEM_ORCHESTRATOR,
        "user": USER_ORCHESTRATOR.format(
            inputs_file=inputs_file,
            formulas_file=formulas_file,
            tables_block=tables_block,
        ),
    }


def build_agent_prompts(
    csv_texts: Dict[str, Any], assignments: Dict[str, str]
) -> Dict[str, Dict[str, str]]:
    tables_block = format_tables_block(csv_texts.get("tables", []))
    return {
        "model_builder": {
            "system": SYSTEM_MODEL_BUILDER,
            "user": USER_MODEL_BUILDER.format(
                assignment=assignment_for("model_builder", assignments),
                inputs_csv=format_csv_block(csv_texts["inputs"]),
                tables_csv=tables_block,
            ),
        },
        "formula_calculation": {
            "system": SYSTEM_FORMULA_CALC,
            "user": USER_FORMULA_CALC.format(
                assignment=assignment_for("formula_calculation", assignments),
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


def assignment_for(agent_id: str, assignments: Dict[str, str]) -> str:
    task = assignments.get(agent_id)
    if task:
        return task
    return "No assignment provided. Follow the standard rules."


SYSTEM_ORCHESTRATOR = (
    "You are the Orchestrator Agent. Return JSON only with key "
    '"assignments". Assign tasks to the other agents.'
)

USER_ORCHESTRATOR = """You coordinate two agents: model_builder and formula_calculation.

You have access to these CSV artifacts:
- Inputs: {inputs_file}
- Formulas: {formulas_file}
- Tables:
{tables_block}

Rules:
- Return JSON only.
- Assign tasks to both agents.
- Keep assignments short and specific to the artifacts.
- Follow this output shape:
  {{
    "assignments": [
      {{"agent_id": "model_builder", "task": "string"}},
      {{"agent_id": "formula_calculation", "task": "string"}}
    ],
    "notes": "optional string"
  }}
"""


SYSTEM_MODEL_BUILDER = (
    "You are the Model Builder Agent. Return JSON only with keys "
    '"inputs" and "tables". Do not include calculations.'
)

USER_MODEL_BUILDER = """Assigned task: {assignment}

Use the CSV artifacts below to build inputs and tables.

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

USER_FORMULA_CALC = """Assigned task: {assignment}

Use the CSV artifact below to build calculations.

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
