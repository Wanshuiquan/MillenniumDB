"""Fixed query templates for telecom (optimized): replaces 0.5 * with 5 *."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluation" / "script"))
from evaluating import telecom as _orig  # noqa: E402


def _fix(s: str) -> str:
    # Replace non-integer LIA coefficient (0.5 -> 5)
    s = s.replace("0.5 *", "5 *")
    # Scale remaining float thresholds by 1000 to match x1000 data conversion
    s = re.sub(r"\b0\.3\b", "300", s)
    s = re.sub(r"\b0\.7\b", "700", s)
    s = re.sub(r"\b0\.1\b", "100", s)
    return s


REGEX_TEMPLATE = [_fix(t) for t in _orig.REGEX_TEMPLATE]
RDPQ_TEMPLATE = [[_fix(q) for q in group] for group in _orig.RDPQ_TEMPLATE]
