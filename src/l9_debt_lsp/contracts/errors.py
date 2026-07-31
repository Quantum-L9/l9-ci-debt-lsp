from __future__ import annotations


class ContractError(ValueError):
    """Base error for LSP consumer contract failures."""


class SchemaValidationError(ContractError):
    """A contract document failed JSON Schema validation."""


class PackCompatibilityError(ContractError):
    """A defense pack is incompatible with this LSP runtime."""
