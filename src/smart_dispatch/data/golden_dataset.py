"""Loader and helpers for the golden test dataset."""

from pathlib import Path
from typing import Optional

from smart_dispatch.data.schemas import GoldenCase

_DEFAULT_PATH = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "golden_transcripts.json"


def load_golden_dataset(path: Optional[Path] = None) -> list[GoldenCase]:
    """Load and validate the golden dataset from JSON.

    Args:
        path: Path to the JSON file.  Defaults to
            ``tests/fixtures/golden_transcripts.json`` relative to the project root.

    Returns:
        List of validated :class:`GoldenCase` instances.

    Raises:
        FileNotFoundError: If the JSON file does not exist at ``path``.
        ValidationError: If any entry fails Pydantic validation.
    """
    resolved = path or _DEFAULT_PATH
    raw = resolved.read_text(encoding="utf-8")
    import json
    data = json.loads(raw)
    return [GoldenCase.model_validate(entry) for entry in data]


def get_duplicates_map(cases: list[GoldenCase]) -> dict[str, list[str]]:
    """Build a mapping from primary call ID to its duplicate call IDs.

    Args:
        cases: Full list of golden cases.

    Returns:
        ``{primary_call_id: [dup_call_id, ...]}`` — only primary calls with at
        least one duplicate are included.
    """
    result: dict[str, list[str]] = {}
    for case in cases:
        dup_of = case.expected.is_duplicate_of
        if dup_of:
            result.setdefault(dup_of, []).append(case.call.call_id)
    return result
