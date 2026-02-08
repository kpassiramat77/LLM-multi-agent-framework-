INPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "value"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "value": {"type": ["number", "string", "boolean", "null"]},
    },
}

TABLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "columns", "rows"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "columns": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": ["number", "null"]},
            },
        },
    },
}

CALCULATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "expression", "references"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "expression": {"type": "string", "minLength": 1},
        "references": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
    },
}

MODEL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["inputs", "tables", "calculations"],
    "properties": {
        "inputs": {"type": "array", "items": INPUT_SCHEMA},
        "tables": {"type": "array", "items": TABLE_SCHEMA},
        "calculations": {"type": "array", "items": CALCULATION_SCHEMA},
    },
}

FRAGMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "inputs": {"type": "array", "items": INPUT_SCHEMA},
        "tables": {"type": "array", "items": TABLE_SCHEMA},
        "calculations": {"type": "array", "items": CALCULATION_SCHEMA},
    },
}
