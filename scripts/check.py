"""Validates the Atlas: every country file against schema.json, plus the rules a schema cannot say."""

import json
import pathlib
import sys
import unicodedata

import jsonschema
import yaml

root = pathlib.Path(__file__).resolve().parent.parent
schema = json.loads((root / "schema.json").read_text())
errors = []
names = {}


def key(name):
    """Name without case or accents, as software compares them."""
    s = unicodedata.normalize("NFKD", name.casefold())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


for path in sorted((root / "countries").glob("*.yml")):
    country = yaml.safe_load(path.read_text())
    for e in jsonschema.Draft202012Validator(schema).iter_errors(country):
        errors.append(f"{path.name}: {e.json_path}: {e.message}")
    if not isinstance(country, dict):
        continue
    if country.get("code") != path.stem:
        errors.append(f"{path.name}: code {country.get('code')!r} differs from the file name")
    for n in country.get("names", []):
        if key(n) in names and names[key(n)] != path.name:
            errors.append(f"{path.name}: {n!r} is also a name in {names[key(n)]}")
        names[key(n)] = path.name
    for r in country.get("records", []):
        if r.get("from") is not None and r.get("until") is not None and r["from"] > r["until"]:
            errors.append(f"{path.name}: {r['type']} ends before it starts")
        years = r.get("years", [])
        if years != sorted(set(years)):
            errors.append(f"{path.name}: {r['type']} years out of order")

if not (root / "countries" / "generic.yml").exists():
    errors.append("countries/generic.yml is missing")
print("\n".join(errors) or f"{len(list((root / 'countries').glob('*.yml')))} files valid")
sys.exit(1 if errors else 0)
