import json
from typing import Any, Dict, List

from jsonschema import Draft202012Validator

from prompt_lab.schemas import FRAGMENT_SCHEMA, MODEL_SCHEMA, ORCHESTRATOR_SCHEMA


def validate_fragment_output(
    raw_text: str, catalog: Dict[str, Any], agent_id: str
) -> Dict[str, Any]:
    report = {
        "agent_id": agent_id,
        "json_only": False,
        "schema_valid": False,
        "references_valid": False,
        "errors": [],
    }
    try:
        parsed = parse_json_only(raw_text)
        report["json_only"] = True
    except ValueError as exc:
        report["errors"].append(str(exc))
        return {"parsed": None, "report": report}

    schema_errors = list(Draft202012Validator(FRAGMENT_SCHEMA).iter_errors(parsed))
    if schema_errors:
        report["errors"].extend(format_schema_errors(schema_errors))
    else:
        report["schema_valid"] = True

    reference_errors = validate_no_invented(parsed, catalog)
    if reference_errors:
        report["errors"].extend(reference_errors)
    else:
        report["references_valid"] = True

    return {"parsed": parsed, "report": report}


def validate_orchestrator_output(
    raw_text: str, allowed_agents: List[str]
) -> Dict[str, Any]:
    report = {
        "agent_id": "orchestrator",
        "json_only": False,
        "schema_valid": False,
        "references_valid": False,
        "errors": [],
    }
    try:
        parsed = parse_json_only(raw_text)
        report["json_only"] = True
    except ValueError as exc:
        report["errors"].append(str(exc))
        return {"parsed": None, "report": report}

    schema_errors = list(
        Draft202012Validator(ORCHESTRATOR_SCHEMA).iter_errors(parsed)
    )
    if schema_errors:
        report["errors"].extend(format_schema_errors(schema_errors))
    else:
        report["schema_valid"] = True

    assignment_errors = validate_orchestrator_assignments(parsed, allowed_agents)
    if assignment_errors:
        report["errors"].extend(assignment_errors)
    else:
        report["references_valid"] = True

    return {"parsed": parsed, "report": report}


def validate_model(model: Dict[str, Any], catalog: Dict[str, Any]) -> Dict[str, Any]:
    report = {
        "schema_valid": False,
        "references_valid": False,
        "errors": [],
    }
    schema_errors = list(Draft202012Validator(MODEL_SCHEMA).iter_errors(model))
    if schema_errors:
        report["errors"].extend(format_schema_errors(schema_errors))
    else:
        report["schema_valid"] = True

    reference_errors = []
    reference_errors.extend(validate_no_invented(model, catalog))
    reference_errors.extend(validate_model_references(model))
    if reference_errors:
        report["errors"].extend(reference_errors)
    else:
        report["references_valid"] = True

    return report


def parse_json_only(raw_text: str) -> Dict[str, Any]:
    if raw_text is None:
        raise ValueError("Empty output from agent")
    text = raw_text.strip()
    if not text:
        raise ValueError("Empty output from agent")

    decoder = json.JSONDecoder()
    obj, idx = decoder.raw_decode(text)
    if text[idx:].strip():
        raise ValueError("Output included non-JSON text")
    if not isinstance(obj, dict):
        raise ValueError("Output must be a JSON object")
    return obj


def validate_no_invented(fragment: Dict[str, Any], catalog: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    known_inputs = {item["name"] for item in catalog.get("inputs", [])}
    known_tables = {item["name"] for item in catalog.get("tables", [])}

    for item in fragment.get("inputs", []) or []:
        name = item.get("name")
        if name and name not in known_inputs:
            errors.append(f"Invented input name: {name}")

    for item in fragment.get("tables", []) or []:
        name = item.get("name")
        if name and name not in known_tables:
            errors.append(f"Invented table name: {name}")

    for item in fragment.get("calculations", []) or []:
        for reference in item.get("references", []) or []:
            if reference not in known_inputs and reference not in known_tables:
                errors.append(f"Invented reference: {reference}")

    return errors


def validate_orchestrator_assignments(
    parsed: Dict[str, Any], allowed_agents: List[str]
) -> List[str]:
    errors: List[str] = []
    assignments = parsed.get("assignments", []) or []
    seen = set()
    allowed = set(allowed_agents)
    for assignment in assignments:
        agent_id = assignment.get("agent_id")
        if not agent_id:
            errors.append("Assignment missing agent_id")
            continue
        if agent_id not in allowed:
            errors.append(f"Unknown agent_id: {agent_id}")
            continue
        if agent_id in seen:
            errors.append(f"Duplicate assignment for agent_id: {agent_id}")
        seen.add(agent_id)

    missing = allowed - seen
    if missing:
        missing_list = ", ".join(sorted(missing))
        errors.append(f"Missing assignments for: {missing_list}")
    return errors


def validate_model_references(model: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    known_inputs = {item["name"] for item in model.get("inputs", [])}
    known_tables = {item["name"] for item in model.get("tables", [])}
    for item in model.get("calculations", []) or []:
        for reference in item.get("references", []) or []:
            if reference not in known_inputs and reference not in known_tables:
                errors.append(f"Reference not in model: {reference}")
    return errors


def format_schema_errors(errors: List[Any]) -> List[str]:
    formatted = []
    for error in errors:
        path = ".".join(str(part) for part in error.path)
        location = f" at {path}" if path else ""
        formatted.append(f"Schema error{location}: {error.message}")
    return formatted
