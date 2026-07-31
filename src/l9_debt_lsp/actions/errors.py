from __future__ import annotations


class CodeActionError(RuntimeError):
    """Base bounded code-action failure."""


class CodeActionSuppressed(CodeActionError):
    """The action is intentionally unavailable."""


class TemplateValidationError(CodeActionError):
    """A remediation template is invalid."""


class EditValidationError(CodeActionError):
    """A text edit is outside the bounded safety contract."""


class EditConflictError(CodeActionError):
    """Two edits overlap or conflict."""


class ProtectedPathError(CodeActionError):
    """A remediation targets a protected path."""


class StaleDiagnosticError(CodeActionError):
    """The diagnostic no longer matches current runtime state."""
