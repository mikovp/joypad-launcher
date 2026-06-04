"""Minimal VDF parser without external vdf dependency."""

import re

_VDF_TOKEN_PATTERN = re.compile(r'"([^"]*)"|\{|\}')


def parse_vdf_simple(path):
    """Minimal VDF parser (no vdf dep): keys and values in quotes, nested {}."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception:
        return None
    text = re.sub(r"//[^\n]*", "", text)
    result = {}
    stack = [result]
    pos = 0
    key = None
    while True:
        m = _VDF_TOKEN_PATTERN.search(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1) is not None:
            tok = m.group(1).strip()
            if key is None:
                key = tok
            else:
                stack[-1][key] = tok
                key = None
        elif m.group(0) == "{":
            new_obj = {}
            if key is not None:
                stack[-1][key] = new_obj
                key = None
            stack.append(new_obj)
        else:
            if len(stack) > 1:
                stack.pop()
    return result if stack else None
