from __future__ import annotations

import difflib

from .models import RemediationTemplate
from .positions import apply_edits

MAX_PREVIEW_CHARACTERS = 200000


def build_preview(
    *,
    relative_path: str,
    text: str,
    template: RemediationTemplate,
) -> tuple[str, str, tuple[str, ...]]:
    updated = apply_edits(
        text=text,
        edits=template.edits,
    )
    diff_lines = difflib.unified_diff(
        text.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{relative_path}",
        tofile=f"b/{relative_path}",
        lineterm="",
    )
    diff = "\n".join(diff_lines)
    limitations = list(template.limitations)
    if len(diff) > MAX_PREVIEW_CHARACTERS:
        diff = diff[: MAX_PREVIEW_CHARACTERS - 1] + "…"
        limitations.append("Preview was truncated to the configured limit.")
    summary = (
        f"{template.title} "
        f"({len(template.edits)} deterministic edit"
        f"{'' if len(template.edits) == 1 else 's'})"
    )
    return (
        summary,
        diff,
        tuple(sorted(set(limitations))),
    )
