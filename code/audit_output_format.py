"""Count strict two-field template compliance on authorized local raw outputs."""
import argparse
import json
from pathlib import Path
import re

from parse_label import LABELS_42, parse_label_from_output


_LABELS = frozenset(LABELS_42)
_TEMPLATE = re.compile(r"[ \t]*证型[：:][ \t]*([^\r\n]+)\r?\n[ \t]*辨证依据[：:][ \t]*([^\r\n]+)")


def complies_with_template(output: str) -> bool:
    """Require exactly two ordered fields, a full in-vocabulary label and a rationale."""
    match = _TEMPLATE.fullmatch(output.strip())
    return bool(match and match[1].strip() in _LABELS and match[2].strip())


def audit_outputs(path: Path) -> dict:
    counts = {"n": 0, "parsed_count": 0, "strict_count": 0}
    with path.open(encoding="utf-8-sig") as records:
        for number, line in enumerate(records, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            output = record.get("raw_output") if isinstance(record, dict) else None
            if not isinstance(output, str):
                raise ValueError(f"Line {number} is missing a string raw_output field")
            counts["n"] += 1
            counts["parsed_count"] += parse_label_from_output(output) != "empty"
            counts["strict_count"] += complies_with_template(output)
    if not counts["n"]:
        raise ValueError("No records found")
    return {
        **counts,
        "valid_label_extraction_rate": counts["parsed_count"] / counts["n"],
        "strict_template_compliance_rate": counts["strict_count"] / counts["n"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, help="Authorized local JSONL with a raw_output field")
    args = parser.parse_args()
    print(json.dumps(audit_outputs(args.jsonl), indent=2))
