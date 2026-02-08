import csv
import os
import re
from typing import Any, Dict, List, Optional


def load_csv_artifacts(manifest: Dict[str, Any]) -> Dict[str, Any]:
    inputs = load_inputs_csv(manifest["inputs_csv"])
    tables = [
        load_table_csv(item["path"], item["name"]) for item in manifest.get("tables", [])
    ]
    formulas = load_formulas_csv(manifest["formulas_csv"])
    return {"inputs": inputs, "tables": tables, "formulas": formulas}


def load_csv_texts(manifest: Dict[str, Any]) -> Dict[str, Any]:
    inputs_path = manifest["inputs_csv"]
    formulas_path = manifest["formulas_csv"]
    return {
        "inputs": {
            "filename": os.path.basename(inputs_path),
            "content": read_text(inputs_path),
        },
        "formulas": {
            "filename": os.path.basename(formulas_path),
            "content": read_text(formulas_path),
        },
        "tables": [
            {
                "name": item["name"],
                "filename": os.path.basename(item["path"]),
                "content": read_text(item["path"]),
            }
            for item in manifest.get("tables", [])
        ],
    }


def load_inputs_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if (
            not reader.fieldnames
            or "key" not in reader.fieldnames
            or "value" not in reader.fieldnames
        ):
            raise ValueError("inputs.csv must have headers: key,value")
        rows = []
        for row in reader:
            key = normalize_text(row.get("key"))
            if not key:
                continue
            value = parse_scalar(row.get("value"))
            rows.append({"name": key, "value": value})
        return rows


def load_table_csv(path: str, name: str) -> Dict[str, Any]:
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        columns = next(reader, [])
        if not columns:
            raise ValueError(f"Table CSV {path} missing header row")
        rows: List[List[Optional[float]]] = []
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            cells = row[: len(columns)] + [""] * max(0, len(columns) - len(row))
            parsed = [parse_float(cell) for cell in cells]
            rows.append(parsed)
        return {"name": name, "columns": [col.strip() for col in columns], "rows": rows}


def load_formulas_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if (
            not reader.fieldnames
            or "name" not in reader.fieldnames
            or "formula" not in reader.fieldnames
        ):
            raise ValueError("formulas.csv must have headers: name,formula")
        rows = []
        for idx, row in enumerate(reader, start=1):
            name = normalize_text(row.get("name"))
            formula = normalize_text(row.get("formula"))
            if not formula:
                continue
            if not name:
                name = f"CalculationRow{idx}"
            rows.append(
                {
                    "name": name,
                    "formula": formula,
                    "source_sheet": normalize_text(row.get("source_sheet")),
                    "cell": normalize_text(row.get("cell")),
                }
            )
        return rows


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def parse_scalar(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    try:
        return float(text)
    except ValueError:
        return text


def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
