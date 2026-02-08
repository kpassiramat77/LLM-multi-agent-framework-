from typing import Any, Dict, Iterable, List


def assemble_model(fragments: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    model = {"inputs": [], "tables": [], "calculations": []}
    model["inputs"] = merge_unique_by_name(
        [item for fragment in fragments if fragment for item in fragment.get("inputs", [])]
    )
    model["tables"] = merge_unique_by_name(
        [item for fragment in fragments if fragment for item in fragment.get("tables", [])]
    )
    model["calculations"] = merge_unique_by_name(
        [
            item
            for fragment in fragments
            if fragment
            for item in fragment.get("calculations", [])
        ]
    )
    return model


def merge_unique_by_name(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    merged = []
    for item in items:
        name = item.get("name")
        if name in seen:
            continue
        merged.append(item)
        seen.add(name)
    return merged
