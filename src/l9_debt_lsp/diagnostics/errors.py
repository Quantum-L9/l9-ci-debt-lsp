from __future__ import annotations


class DiagnosticError(RuntimeError):
    """Base diagnostic projection failure."""


class FindingValidationError(DiagnosticError):
    """An SDK finding violates the public consumer contract."""


class SourceLocationError(DiagnosticError):
    """A finding source location cannot be represented safely."""


class DiagnosticPublicationError(DiagnosticError):
    """A diagnostic publication could not be committed safely."""
