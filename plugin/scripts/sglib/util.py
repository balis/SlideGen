"""Shared helpers: JSON I/O with schema validation, manifests, slide ranges."""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

import jsonschema
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = PLUGIN_ROOT / "schemas"


class SgError(Exception):
    """A violated invariant. The message tells the caller what to fix or re-run."""


@lru_cache(maxsize=None)
def _schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _registry():
    """All schemas, so that one schema can reference another by its urn:slidegen: id."""
    from referencing import Registry, Resource
    resources = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resources.append((contents["$id"], Resource.from_contents(contents)))
    return Registry().with_resources(resources)


def load_json(path: Path, schema: str | None = None):
    path = Path(path)
    if not path.exists():
        raise SgError(f"missing file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SgError(f"{path}: invalid JSON at line {e.lineno}: {e.msg}") from e
    if schema:
        validator = jsonschema.Draft202012Validator(_schema(schema), registry=_registry())
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        if errors:
            details = "; ".join(f"/{'/'.join(map(str, e.absolute_path))}: {e.message}"
                                for e in errors[:5])
            raise SgError(f"{path} does not match schema '{schema}': {details}")
    return data


def check_schema(data, schema: str, where) -> None:
    """Raise SgError listing the first violations of a schema (for data that is not read from a JSON file)."""
    validator = jsonschema.Draft202012Validator(_schema(schema), registry=_registry())
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        details = "; ".join(f"/{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors[:5])
        raise SgError(f"{where} does not match schema '{schema}': {details}")


def write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def parse_range(spec) -> list[int]:
    """'36-49' -> [36..49]; '53' -> [53]; 53 -> [53]; '3,5-6' -> [3, 5, 6]."""
    out: list[int] = []
    for part in str(spec).split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def load_manifest(path: Path) -> dict:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for deck in data.get("decks", []):
        deck["_path"] = (path.parent / deck["path"]).resolve()
        deck["_out_of_scope"] = sorted({i for r in deck.get("out_of_scope", [])
                                        for i in parse_range(r["slides"])})
        deck["_recreate"] = [{**r, "_slides": parse_range(r["slides"])}
                             for r in deck.get("recreate", [])]
        deck["_protected"] = deck.get("protected", [])
    return data


def manifest_deck(manifest: dict, deck_id: str) -> dict:
    for deck in manifest.get("decks", []):
        if deck["id"] == deck_id:
            return deck
    raise SgError(f"deck '{deck_id}' is not in the manifest")


def excluded_slides(slides_doc: dict, deck_cfg: dict | None) -> dict[int, str]:
    """Slides not to check, mapped to the reason."""
    out: dict[int, str] = {}
    skip_hidden = (deck_cfg or {}).get("hidden_slides", "skip") == "skip"
    for s in slides_doc["slides"]:
        if skip_hidden and s["hidden"]:
            out[s["index"]] = "hidden"
    for i in (deck_cfg or {}).get("_out_of_scope", []):
        out[i] = "out of scope"
    return out


def today() -> str:
    return date.today().isoformat()
