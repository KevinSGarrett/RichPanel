"""Strict JSON schema validation helpers."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from jsonschema import Draft7Validator, ValidationError as JsonSchemaValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "docs" / "04_LLM_Design_Evaluation" / "schemas"


class SchemaValidationError(RuntimeError):
    """Raised when an LLM output fails schema validation."""

    def __init__(self, schema_name: str, errors: Tuple[str, ...]):
        joined = "; ".join(errors)
        super().__init__(f"Schema {schema_name} validation failed: {joined}")
        self.schema_name = schema_name
        self.errors = errors


def _load_schema(schema_name: str) -> Dict[str, Any]:
    schema_path = SCHEMA_DIR / f"{schema_name}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=4)
def _schema_and_validator(schema_name: str) -> Tuple[Dict[str, Any], Draft7Validator]:
    schema = _load_schema(schema_name)
    validator = Draft7Validator(schema)
    return schema, validator


def validate_payload(schema_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    schema, validator = _schema_and_validator(schema_name)
    errors = tuple(error.message for error in validator.iter_errors(payload))
    if errors:
        raise SchemaValidationError(schema_name, errors)
    return payload


def validate_decision_schema(payload: Dict[str, Any]) -> Dict[str, Any]:
    return validate_payload("mw_decision_v1", payload)


def validate_tier2_schema(payload: Dict[str, Any]) -> Dict[str, Any]:
    return validate_payload("mw_tier2_verifier_v1", payload)


def get_schema_dict(schema_name: str) -> Dict[str, Any]:
    schema, _ = _schema_and_validator(schema_name)
    return schema
