from __future__ import annotations


class TelemetryError(RuntimeError):
    """Base telemetry failure."""


class TelemetryDisabled(TelemetryError):
    """Telemetry is disabled by policy."""


class TelemetryPolicyError(TelemetryError):
    """Telemetry policy is invalid or inconsistent."""


class TelemetryPrivacyError(TelemetryError):
    """Telemetry contains prohibited data."""


class TelemetryStorageError(TelemetryError):
    """Telemetry could not be persisted safely."""


class TelemetryTransportError(TelemetryError):
    """Telemetry could not be delivered."""
