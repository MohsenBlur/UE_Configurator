"""Utility helpers for UI components."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


def infer_cvar_type(
    range_str: str, default: str
) -> Tuple[str, Optional[float], Optional[float], Optional[List[str]]]:
    """Infer data type and range information for a CVar value.

    Parameters
    ----------
    range_str:
        Raw range string from the indexer (e.g. ``"0-1"`` or ``"Low|High"``).
    default:
        Default value string from the indexer.

    Returns
    -------
    tuple
        ``(dtype, minimum, maximum, options)`` where ``dtype`` is one of
        ``"int"``, ``"float"`` or ``"str"``. ``options`` contains a list of
        allowed string values when ``dtype`` is ``"str"`` and the range string
        represents an enumeration.
    """

    range_str = range_str.strip()

    # Try to parse a numeric range like ``0-1`` or ``0..1``.
    num_match = re.match(
        r"^\s*([+-]?\d+(?:\.\d+)?)\s*(?:-|\.\.)\s*([+-]?\d+(?:\.\d+)?)\s*$",
        range_str,
    )
    if num_match:
        start, end = num_match.groups()
        if "." in start or "." in end:
            return "float", float(start), float(end), None
        return "int", int(start), int(end), None

    # If the range isn't numeric, treat it as a set of string options
    # separated by common delimiters (|, /, ,).
    if range_str:
        parts = [p.strip() for p in re.split(r"[|,/]", range_str) if p.strip()]
        if len(parts) > 1:
            return "str", None, None, parts

    # Fall back to the default value to guess type when no range was parsed.
    try:
        if "." in default or "e" in default.lower():
            float(default)
            return "float", None, None, None
        int(default)
        return "int", None, None, None
    except Exception:
        return "str", None, None, None

