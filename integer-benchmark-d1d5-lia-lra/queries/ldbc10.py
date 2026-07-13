"""Fixed query templates for ldbc10 (optimized): replaces 0.5 * with 5 *."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluation" / "script"))
from evaluating import ldbc10 as _orig  # noqa: E402


def _fix(s: str) -> str:
    return s.replace("0.5 *", "5 *")


REGEX_TEMPLATE = [_fix(t) for t in _orig.REGEX_TEMPLATE]
RDPQ_TEMPLATE = [[_fix(q) for q in group] for group in _orig.RDPQ_TEMPLATE]
