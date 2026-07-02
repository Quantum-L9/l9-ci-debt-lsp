"""Compute LSP diagnostics by running each rule against document text."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)

_SEVERITY_MAP: dict[str, DiagnosticSeverity] = {
    "error": DiagnosticSeverity.Error,
    "warning": DiagnosticSeverity.Warning,
    "info": DiagnosticSeverity.Information,
    "hint": DiagnosticSeverity.Hint,
}

_LANG_EXT_MAP: dict[str, list[str]] = {
    "yaml": [".yml", ".yaml"],
    "python": [".py"],
    "toml": [".toml"],
}


def _file_matches_language(uri: str, languages: list[str]) -> bool:
    suffix = Path(uri.replace("file://", "")).suffix.lower()
    for lang in languages:
        if suffix in _LANG_EXT_MAP.get(lang, []):
            return True
    return False


def _line_range(text: str, match: re.Match) -> Range:  # type: ignore[type-arg]
    start_pos = match.start()
    line_number = text[:start_pos].count("\n")
    line_start = text.rfind("\n", 0, start_pos) + 1
    col_start = start_pos - line_start
    col_end = col_start + len(match.group(0))
    return Range(
        start=Position(line=line_number, character=col_start),
        end=Position(line=line_number, character=col_end),
    )


def compute_diagnostics(
    text: str,
    uri: str,
    rules: list[dict[str, Any]],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []

    for rule in rules:
        if not _file_matches_language(uri, rule.get("language", [])):
            continue

        positive_patterns: list[str] = rule.get("patterns", [])
        negative_patterns: list[str] = rule.get("negative_patterns", [])

        for pos_pattern in positive_patterns:
            for match in re.finditer(pos_pattern, text, re.MULTILINE):
                # Check whether any negative pattern is present in the
                # vicinity (within 20 lines) of the match — avoids false
                # positives on files that already have the fix applied.
                match_start = text[:match.start()].count("\n")
                lines = text.splitlines()
                window_start = max(0, match_start - 2)
                window_end = min(len(lines), match_start + 20)
                window_text = "\n".join(lines[window_start:window_end])

                suppressed = any(
                    re.search(neg, window_text)
                    for neg in negative_patterns
                )
                if suppressed:
                    continue

                severity = _SEVERITY_MAP.get(
                    rule.get("severity", "warning"),
                    DiagnosticSeverity.Warning,
                )
                diagnostics.append(
                    Diagnostic(
                        range=_line_range(text, match),
                        message=rule.get("message", f"Rule {rule.get('id')} violation"),
                        severity=severity,
                        source="l9-ci-debt-lsp",
                        code=rule.get("id"),
                    )
                )

    return diagnostics
