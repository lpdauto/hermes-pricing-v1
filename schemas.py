"""PRICING_V1 tool schema."""

PRICING_V1 = {
    "name": "pricing_v1",
    "description": "Deterministic auction max-hammer calculator using approved PRICING_V1 rules.",
    "parameters": {
        "type": "object",
        "properties": {
            "make": {"type": "string"},
            "model": {"type": "string"},
            "year": {"type": "integer"},
            "engine": {"type": "string"},
            "mileage": {"type": ["integer", "null"]},
            "mileage_status": {"type": "string"},
            "run_status": {"type": "string"},
            "front_risk": {
                "type": "string",
                "enum": ["NORMAL_MODERATE", "BORDERLINE", "SEVERE"],
            },
        },
        "required": ["make", "model", "year", "engine", "run_status", "front_risk"],
    },
}
