# ADR-LSP-023: Telemetry storage is durable and bounded
- Status: Accepted
- Phase: LSP-P5
## Decision
Telemetry events are written atomically as immutable canonical JSON documents.
The local queue is bounded by event count, byte size, and retention age.
Overflow removes the oldest queued events and degrades telemetry health without
affecting editor behavior.
