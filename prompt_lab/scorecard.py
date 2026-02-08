from typing import Any, Dict


def build_scorecard(
    catalog: Dict[str, Any],
    agent_outputs: Dict[str, Any],
    model_validation: Dict[str, Any],
) -> Dict[str, Any]:
    agent_scores = {}
    for agent_id, payload in agent_outputs.items():
        validation = payload["validation"]
        agent_scores[agent_id] = {
            "json_only": validation.get("json_only", False),
            "schema_valid": validation.get("schema_valid", False),
            "references_valid": validation.get("references_valid", False),
            "errors": validation.get("errors", []),
        }

    all_agent_passed = all(
        score["json_only"] and score["schema_valid"] and score["references_valid"]
        for score in agent_scores.values()
    )
    model_passed = model_validation.get("schema_valid") and model_validation.get(
        "references_valid"
    )

    return {
        "counts": {
            "inputs": len(catalog.get("inputs", [])),
            "tables": len(catalog.get("tables", [])),
            "formulas": len(catalog.get("formulas", [])),
        },
        "agents": agent_scores,
        "model": model_validation,
        "all_passed": all_agent_passed and model_passed,
    }


def format_scorecard(scorecard: Dict[str, Any], output_path: str) -> str:
    lines = []
    lines.append("Prompt Lab Scorecard")
    lines.append("--------------------")
    lines.append(
        "Loaded: "
        f"{scorecard['counts']['inputs']} inputs, "
        f"{scorecard['counts']['tables']} tables, "
        f"{scorecard['counts']['formulas']} formulas"
    )
    lines.append("")

    for agent_id, score in scorecard["agents"].items():
        status = "PASS" if (
            score["json_only"] and score["schema_valid"] and score["references_valid"]
        ) else "FAIL"
        lines.append(f"Agent {agent_id}: {status}")
        lines.append(
            f"  JSON only: {score['json_only']}, "
            f"schema: {score['schema_valid']}, "
            f"references: {score['references_valid']}"
        )
        if score["errors"]:
            for error in score["errors"]:
                lines.append(f"  - {error}")
        lines.append("")

    model_status = "PASS" if (
        scorecard["model"].get("schema_valid")
        and scorecard["model"].get("references_valid")
    ) else "FAIL"
    lines.append(f"Model validation: {model_status}")
    if scorecard["model"].get("errors"):
        for error in scorecard["model"]["errors"]:
            lines.append(f"  - {error}")

    lines.append("")
    lines.append(f"Output saved to: {output_path}")
    lines.append(f"Overall: {'PASS' if scorecard['all_passed'] else 'FAIL'}")
    return "\n".join(lines)
