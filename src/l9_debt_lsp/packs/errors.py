from __future__ import annotations


class PackError(RuntimeError):
    """Base pack lifecycle failure."""


class ManifestValidationError(PackError):
    """The publication manifest is invalid."""


class TrustError(PackError):
    """The pack signer is not trusted."""


class SignatureError(PackError):
    """The pack signature is invalid."""


class ArchiveSecurityError(PackError):
    """The archive violates extraction security policy."""


class ArchiveIntegrityError(PackError):
    """The archive or one of its members failed integrity validation."""


class PackValidationError(PackError):
    """The extracted defense pack is invalid."""


class PackCompatibilityFailure(PackError):
    """The defense pack is incompatible with this runtime."""


class PackRetiredError(PackError):
    """The requested defense pack has been retired."""


class ImmutablePackCollisionError(PackError):
    """An existing pack identity contains different immutable content."""


class ActivationError(PackError):
    """Pack activation could not be completed atomically."""


class RollbackError(PackError):
    """Previous-known-good rollback could not be completed."""
